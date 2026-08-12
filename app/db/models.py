"""
Modelos ORM (SQLAlchemy 2.x) que mapean 1:1 el DDL ya aplicado en 
`BreteAI-Infra/db/init/001_schema.sql` (ver también docs/design.md §3).

Tablas modeladas, en este orden de dependencia:
1. Corrida        (tabla `corridas`)
2. OfertaRaw       (tabla `ofertas_raw`)      — FK a Corrida
3. Oferta          (tabla `ofertas`)          — FK a OfertaRaw, self-FK `similar_a`
4. OfertaHistorial (tabla `oferta_historial`) — FK a Oferta, ON DELETE CASCADE
5. Comentario      (tabla `comentarios`)      — FK a Oferta, ON DELETE CASCADE
6. Adjunto         (tabla `adjuntos`)         — FK a Oferta, ON DELETE CASCADE
7. FeedbackIA      (tabla `feedback_ia`)      — FK a Oferta, ON DELETE CASCADE
8. Correo          (tabla `correos`)          — sin FK, `oferta_ids` es ARRAY(BigInteger)

Reglas:
- Los nombres de columna y tipos DEBEN coincidir exactamente con el SQL ya
  aplicado — no es este archivo el que define el schema, el schema ya existe
  en la DB. Si algo no cuadra, el problema está en el DDL, no acá: no
  improvises columnas nuevas.
- `estado_proc` en OfertaRaw y `estado` en Oferta: usar `Enum` de Python +
  `String` en DB (no crear un tipo ENUM de Postgres nuevo, el DDL ya usa TEXT
  con CHECK/default por convención de valores, mantené esa convención).
- Una sola `Base` declarativa para todo el proyecto (DRY) — no crear una
  `Base` por archivo.
"""

from typing import Optional, List
from sqlalchemy import BigInteger, Boolean, Date, DateTime, JSON, Numeric, SmallInteger, String, Text, ARRAY, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from enum import Enum as PyEnum

# Base declarativa compartida para todo el proyecto
class Base(DeclarativeBase):
    pass

class EstadoProceso(str, PyEnum):
    pendiente = "pendiente"
    procesada = "procesada" 
    error = "error"
    descartada = "descartada"

class EstadoOferta(str, PyEnum):
    nueva = "nueva"
    vista = "vista"
    aplicada = "aplicada"
    enProceso = "enProceso"
    enEspera = "enEspera"
    respondida = "respondida" 
    rechazada = "rechazada"

# Modelo para la tabla `corridas`
class Corrida(Base):
    __tablename__ = 'corridas'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    inicio: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    fin: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default='enCurso')
    fuentes_ok: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    fuentes_error: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    notas: Mapped[Optional[str]] = mapped_column(Text)

# Modelo para la tabla `ofertas_raw` 
class OfertaRaw(Base):
    __tablename__ = 'ofertas_raw'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    corrida_id: Mapped[int] = mapped_column(ForeignKey('corridas.id'))
    fuente: Mapped[str] = mapped_column(String(20), nullable=False)
    id_externo: Mapped[str] = mapped_column(String(100), nullable=False) 
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    obtenida_en: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    estado_proc: Mapped[str] = mapped_column(String(20), nullable=False, default='pendiente')
    error_msg: Mapped[Optional[str]] = mapped_column(Text)
    intentos: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    
    # Relación con corrida
    corrida: Mapped["Corrida"] = relationship("Corrida", back_populates="ofertas_raw")
    # Relación inversa con Oferta (una raw puede derivar en una oferta procesada)
    ofertas: Mapped[List["Oferta"]] = relationship("Oferta", back_populates="raw")

    # El índice parcial idx_raw_cola (estado_proc = 'pendiente') ya existe en
    # la DB vía db/init/001_schema.sql — no se redeclara acá para no duplicar.

# Modelo para la tabla `ofertas`
class Oferta(Base):
    __tablename__ = 'ofertas'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    raw_id: Mapped[int] = mapped_column(ForeignKey('ofertas_raw.id'), nullable=False) 
    fuente: Mapped[str] = mapped_column(String(20), nullable=False)
    id_externo: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Campos canónicos
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    empresa: Mapped[Optional[str]] = mapped_column(Text) 
    ubicacion: Mapped[Optional[str]] = mapped_column(Text)
    pais: Mapped[Optional[str]] = mapped_column(Text)
    modalidad: Mapped[Optional[str]] = mapped_column(String(20))
    
    salario_min: Mapped[Optional[Numeric]] = mapped_column(Numeric(precision=15, scale=2))
    salario_max: Mapped[Optional[Numeric]] = mapped_column(Numeric(precision=15, scale=2)) 
    salario_moneda: Mapped[Optional[str]] = mapped_column(String(10))
    salario_estimado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False) 
    fecha_publicacion: Mapped[Optional[Date]] = mapped_column(Date)
    
    # Campos de IA
    resumen: Mapped[Optional[str]] = mapped_column(Text)
    requisitos: Mapped[Optional[List[dict]]] = mapped_column(JSON)
    beneficios: Mapped[Optional[List[dict]]] = mapped_column(JSON) 
    seniority: Mapped[Optional[str]] = mapped_column(String(20))
    empresa_real: Mapped[Optional[str]] = mapped_column(Text)
    
    # El CHECK (score BETWEEN 0 AND 100) ya existe en la DB vía el DDL — no
    # se redeclara acá (mapped_column no acepta `check` como kwarg directo).
    score: Mapped[Optional[int]] = mapped_column(SmallInteger)
    score_razon: Mapped[Optional[str]] = mapped_column(Text)
    
    # Campos de gestión
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default='nueva') 
    etiquetas: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    similar_a: Mapped[Optional[int]] = mapped_column(ForeignKey('ofertas.id'))
    
    creada_en: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actualizada_en: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    raw: Mapped["OfertaRaw"] = relationship("OfertaRaw", back_populates="ofertas")

    # Los índices (estado, score DESC, empresa, modalidad) ya existen en la
    # DB vía db/init/001_schema.sql — no se redeclaran acá.

# Modelo para la tabla `oferta_historial`
class OfertaHistorial(Base):
    __tablename__ = 'oferta_historial'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    oferta_id: Mapped[int] = mapped_column(ForeignKey('ofertas.id', ondelete='CASCADE'), nullable=False) 
    de_estado: Mapped[Optional[str]] = mapped_column(String(20))
    a_estado: Mapped[str] = mapped_column(String(20), nullable=False)
    en: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

# Modelo para la tabla `comentarios`  
class Comentario(Base):
    __tablename__ = 'comentarios'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    oferta_id: Mapped[int] = mapped_column(ForeignKey('ofertas.id', ondelete='CASCADE'), nullable=False) 
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    creado_en: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

# Modelo para la tabla `adjuntos`
class Adjunto(Base):
    __tablename__ = 'adjuntos'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    oferta_id: Mapped[int] = mapped_column(ForeignKey('ofertas.id', ondelete='CASCADE'), nullable=False) 
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    ruta: Mapped[str] = mapped_column(Text, nullable=False)
    subido_en: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

# Modelo para la tabla `feedback_ia`
class FeedbackIA(Base):
    __tablename__ = 'feedback_ia'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    oferta_id: Mapped[int] = mapped_column(ForeignKey('ofertas.id', ondelete='CASCADE'), nullable=False) 
    campo: Mapped[str] = mapped_column(Text, nullable=False)
    valor_ia: Mapped[Optional[str]] = mapped_column(Text)
    valor_correcto: Mapped[Optional[str]] = mapped_column(Text)
    nota: Mapped[Optional[str]] = mapped_column(Text)
    creado_en: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

# Modelo para la tabla `correos`
class Correo(Base):
    __tablename__ = 'correos'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    enviado_en: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    oferta_ids: Mapped[List[int]] = mapped_column(ARRAY(BigInteger), nullable=False)

# Relación inversa desde Corrida a OfertaRaw
Corrida.ofertas_raw = relationship("OfertaRaw", order_by=OfertaRaw.id, back_populates="corrida")
