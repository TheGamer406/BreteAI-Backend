"""
Módulo de conectores ATS (Greenhouse, Lever, Ashby) para obtener ofertas de trabajo.

Este módulo implementa:
1. La clase base `BaseConnector` con métodos comunes a todos los conectores
2. Los tres conectores específicos: Greenhouse, Lever y Ashby
3. El modelo canónico `OfertaCanonica` que define la estructura común de las ofertas

Los conectores deben implementar:
- Método `run()` para obtener las ofertas desde la fuente ATS
- Método `parse_oferta()` para convertir los datos brutos en el formato canónico  
- Validación del modelo canónico con `validate_model()`

El pipeline completo debe procesar las ofertas usando este módulo antes de guardarlas 
en la base de datos.
"""