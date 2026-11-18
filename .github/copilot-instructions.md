# Reglas de Gobernanza Operativa y Contexto de Proyecto (AGENTS.md)

## 1. Clasificación de Información y Seguridad Técnicas
- **Secretos técnicos estrictamente protegidos**: Queda prohibido leer, exponer o incluir datos reales de archivos `.env`, `SECRET_KEY`, credenciales de base de datos o tokens de API en las respuestas.
- **Uso de placeholders**: Ante la necesidad de referenciar claves o secretos en ejemplos, utiliza siempre valores simulados (ej. `SECRET_KEY = 'django-insecure-placeholder'`).
- **Archivos protegidos**: No modificar la configuración de producción (`settings.py`,'settings_local.py') ni archivos de migración existentes sin autorización explícita.

## 2. Contexto de Arquitectura de la Aplicación
- **Entorno de ejecución**: Python 3.x + Django framework en Visual Studio.
- **Patrón de diseño**: MVT (Model-View-Template).
- **Estructura de capas**:
  - Los modelos (`models.py`) definen la lógica de datos y validaciones de campo.
  - La lógica de formularios debe residir en `forms.py` (usando `ModelForm` cuando aplique).
  - Las vistas (`views.py`) deben ser limpias: priorizar vistas basadas en clases (*Class-Based Views*) o funciones bien delimitadas.
  - Las rutas deben declararse explícitamente en `urls.py` usando `path` con nombres de ruta (*name*).

## 3. Estilo de Código y Buenas Prácticas
- Seguir las normas de estilo PEP 8 para código Python.
- Incluir comprobaciones de tipos (*type hinting*) en funciones y métodos auxiliares.
- Gestionar excepciones de Django de forma explícita (ej. `ObjectDoesNotExist`, `ValidationError`).

## 4. Validación y Evidencia de Código
- Todo nuevo módulo, vista o modelo generado debe incluir sus correspondientes pruebas unitarias en `tests.py` utilizando el cliente de pruebas de Django (`django.test.TestCase`).
- Antes de dar por finalizada una tarea, el código debe ser ejecutable y pasar la validación con `python manage.py test`.

### 5. Mantenimiento de la Documentación (`docs/`)
- **Sincronización obligatoria**: Cada vez que crees o modifiques un modelo de Django (en `models.py`) o implementes una nueva regla de negocio, debes actualizar obligatoriamente los archivos correspondientes en `docs/` (`docs/database.md`, `docs/business_rules.md` o `docs/architecture.md`) dentro del mismo cambio.