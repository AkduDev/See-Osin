# Contribuir a See-OSIN

Gracias por tu interés en contribuir a See-OSIN! Este documento explica cómo contribuir al proyecto.

## Reglas Importantes

### 🔒 Aprobación Requerida

**Todas las contribuciones requieren aprobación del maintainer antes de ser mergeadas.**

- Los Pull Requests serán revisados por el maintainer
- El maintainer tiene la decisión final sobre qué se acepta
- Los cambios pueden ser solicitados antes de la aprobación

### ✅ Qué se Acepta

- **Bug fixes** - Corrección de errores
- **Nuevas funcionalidades** - Que sigan la arquitectura del proyecto
- **Mejoras de rendimiento** - Optimizaciones
- **Documentación** - Mejoras al docs
- **Tests** - Cobertura de tests

### ❌ Qué NO se Acepta

- **Spam** - Cualquier forma de spam
- **Malware** - Código malicioso
- **Cambios que rompan la arquitectura** - Sin discusión previa
- **Features no relacionadas** - Mantener el foco del proyecto

---

## Flujo de Trabajo

### 1. Preparar el Entorno

```bash
# Clonar el repositorio
git clone https://github.com/AkduDev/See-Osin.git
cd See-Osin

# Crear virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -e ".[dev]"
```

### 2. Crear una Rama

```bash
# Siempre crear una rama nueva para cada feature/fix
git checkout -b feature/nombre-descriptivo
# o
git checkout -b fix/nombre-del-bug
```

**Nomenclatura de ramas:**
- `feature/` - Nuevas funcionalidades
- `fix/` - Corrección de bugs
- `docs/` - Documentación
- `refactor/` - Refactorización
- `test/` - Tests

### 3. Hacer los Cambios

- Seguir el estilo de código existente
- Escribir código limpio y documentado
- Agregar tests para nuevas funcionalidades
- Actualizar documentación si es necesario

### 4. Commit

```bash
# Ver qué se va a commitear
git status

# Agregar archivos
git add .

# Hacer commit con mensaje descriptivo
git commit -m "feat: agregar nueva funcionalidad X"
```

**Formato de commits:**
- `feat:` - Nueva funcionalidad
- `fix:` - Corrección de bug
- `docs:` - Documentación
- `style:` - Formato (no afecta el código)
- `refactor:` - Refactorización
- `test:` - Tests
- `chore:` - Tareas de mantenimiento

### 5. Push y Pull Request

```bash
# Push a tu rama
git push origin feature/nombre-descriptivo
```

Luego en GitHub:
1. Ir al repositorio
2. Click en "New Pull Request"
3. Seleccionar tu rama
4. Escribir un título descriptivo
5. Describir los cambios en el cuerpo
6. Click en "Create Pull Request"

---

## Estructura del Proyecto

```
src/see/
├── core/                 # Motor principal
│   ├── types.py          # Tipos compartidos
│   ├── registry.py       # Registro de módulos
│   └── engine.py         # Motor OSINT
│
├── modules/              # Dominios OSINT
│   ├── base.py           # Clases base
│   │
│   ├── phones/           # Módulo de teléfonos
│   │   ├── domain.py     # Lógica de dominio
│   │   └── providers/    # Proveedores API
│   │
│   ├── emails/           # (futuro) Módulo de emails
│   ├── people/           # (futuro) Módulo de personas
│   └── domains/          # (futuro) Módulo de dominios
│
├── output/               # Manejo de salida
└── utils/                # Utilidades
```

---

## Agregar un Nuevo Módulo

### 1. Crear Estructura

```bash
mkdir -p src/see/modules/mi-modulo/providers
touch src/see/modules/mi-modulo/__init__.py
touch src/see/modules/mi-modulo/domain.py
touch src/see/modules/mi-modulo/providers/__init__.py
touch src/see/modules/mi-modulo/providers/base.py
```

### 2. Crear Domain

```python
# modules/mi-modulo/domain.py
from see.modules.base import BaseModule
from see.core.types import BaseResult

class MiModuloDomain(BaseModule):
    @property
    def name(self) -> str:
        return "mi-modulo"
    
    @property
    def description(self) -> str:
        return "Descripción del módulo"
    
    @property
    def domain(self) -> str:
        return "mi-modulo"
    
    def is_available(self) -> bool:
        return True
    
    async def scan(self, target: str, **kwargs) -> BaseResult:
        # Implementar lógica
        pass
```

### 3. Crear Provider

```python
# modules/mi-modulo/providers/mi-provider.py
from see.modules.base import BaseProvider
from see.core.types import BaseResult

class MiProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "mi-provider"
    
    @property
    def requires_api_key(self) -> bool:
        return False
    
    def is_available(self) -> bool:
        return True
    
    async def scan(self, target: str, **kwargs) -> BaseResult:
        # Implementar lógica
        pass
```

### 4. Registrar Módulo

```python
# modules/__init__.py
from see.core.registry import register_module
from see.modules.mi-modulo.domain import MiModuloDomain

register_module(MiModuloDomain())
```

---

## Estilo de Código

### Python

- Seguir PEP 8
- Usar type hints
- Docstrings para funciones públicas
- Máximo 120 caracteres por línea

### Ejemplo

```python
async def get_carrier(self, phone: str, config: AppConfig) -> CarrierResult | None:
    """
    Get carrier information for phone number.
    
    Args:
        phone: Phone number in E.164 format
        config: Application configuration
    
    Returns:
        CarrierResult with carrier information, or None if not found
    """
    try:
        # Implementation
        pass
    except Exception as e:
        logger.error(f"Failed to get carrier: {e}")
        return None
```

---

## Tests

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=see

# Tests específicos
pytest tests/test_phones.py
```

### Escribir Tests

```python
# tests/test_mi_modulo.py
import pytest
from see.modules.mi_modulo.domain import MiModuloDomain

@pytest.mark.asyncio
async def test_scan():
    domain = MiModuloDomain()
    result = await domain.scan("test-target")
    assert result is not None
    assert result.success is True
```

---

## Issues

### Reportar Bugs

Incluir:
1. Pasos para reproducir
2. Comportamiento esperado
3. Comportamiento actual
4. Versión de Python
5. Sistema operativo

### Solicitar Features

Incluir:
1. Descripción de la funcionalidad
2. Caso de uso
3. Ejemplos de cómo se usaría

---

## Pull Requests

### Checklist

- [ ] Código sigue el estilo del proyecto
- [ ] Tests incluidos (si aplica)
- [ ] Documentación actualizada (si aplica)
- [ ] Commits con formato correcto
- [ ] Descripción clara en el PR
- [ ] No rompe funcionalidad existente

### Formato del PR

```
## Descripción
Breve descripción de los cambios

## Tipo de Cambio
- [ ] Bug fix
- [ ] Nueva funcionalidad
- [ ] Refactorización
- [ ] Documentación
- [ ] Otro

## Testing
- [ ] Tests existentes pasan
- [ ] Nuevos tests incluidos

## Notas
Cualquier información adicional
```

---

## Preguntas?

Si tienes preguntas sobre cómo contribuir, abre un issue con la etiqueta `question`.
