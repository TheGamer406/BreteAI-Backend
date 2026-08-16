"""
TODO (Fase 2): carga y parseo de `resources/perfil.toon` (el perfil del
candidato que la IA usa como contexto para puntuar).

Qué implementar acá:
- `cargar_perfil(ruta: Path | None = None) -> Perfil`: lee el TOON y lo
  devuelve como objeto. Cachear con `functools.lru_cache` (se lee una vez por
  proceso, no una vez por oferta — el worker procesa cientos).
- `class Perfil(BaseModel)`: modelo de los campos que el prompt necesita.
  Ver `config/perfil.example.toon` para la estructura completa; los que más
  pesan en el score son:
    candidato.seniority, candidato.resumen
    intereses_rol[], skills_tecnicos.*
    preferencias.modalidades[], preferencias.ubicaciones_aceptadas[],
    preferencias.reubicacion_internacional, preferencias.salario.*,
    preferencias.keywords[], preferencias.excluir[]
    criterios_match.* (pesos + penalizar[] + bonificar[])
- Fallback claro: si `resources/perfil.toon` no existe (ej: alguien clonó el
  repo y no copió la plantilla), lanzar un error explícito diciendo
  "copiá config/perfil.example.toon a resources/perfil.toon", NO seguir con
  un perfil vacío (puntuaría todo mal y en silencio).

Sobre TOON: es un formato compacto tipo YAML con arrays tipados
(`idiomas[2]{idioma,nivel}:`). Evaluar al implementar si hay una librería
que lo parsee o si conviene un parser propio mínimo para el subconjunto que
usa la plantilla. Si el parser propio empieza a crecer, es señal de que
convenía otro formato — anotarlo, no seguir agrandándolo en silencio.

PRIVACIDAD: `resources/` está gitignored y contiene datos personales reales.
Este módulo lee de ahí, pero **nada de su contenido debe terminar en logs**
(ni siquiera en DEBUG) ni en mensajes de error.
"""
