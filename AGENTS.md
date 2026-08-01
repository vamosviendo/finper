# AGENTS.md - Development Guidelines for wlili

This file provides guidance for AI agents working on this codebase.

## Project Overview

- **Type**: Django Accounting system (sistema contable)
- **Python**: 3.x
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Testing**: pytest + Selenium (functional tests)

---

## Build / Lint / Test Commands

### Django Management

```bash
# Run development server
python src/manage.py runserver

# Apply migrations
python src/manage.py migrate

# Create migrations
python src/manage.py makemigrations

# Collect static files
python src/manage.py collectstatic --noinput
```

### Running Tests

```bash
# Run all tests
pytest

# Run a single test file
pytest base/tests.py

# Run a single test class
pytest base/tests.py::FooterFunctionalTests

# Run a single test method
pytest base/tests.py::FooterFunctionalTests::test_footer_renders_without_error

# Run unit/integration tests only (excludes functional tests)
pytest -k "not FunctionalTest"

# Run functional tests only (Selenium)
pytest functional_tests/

# Run tests with verbose output
pytest -v

# Run tests without reusing DB
pytest --reuse-db --no-migrateci
```

### Running the Development Server

```bash
python manage.py runserver
```

---

## General behavior
- Atenerse al modo Plan a menos que esté seleccionado explicitamente el modo build
- No aplicar directamente cambios al código, sino presentarlos en pantalla para su revisión. Indicar con un comentario los lugares específicos del código en los que se han hecho cambios.
- Cuando falte información, solicitarla. Comprobar en vez de inferir o suponer. Empiria.

---

## Code Style Guidelines

### General Principles

- **Minuciosidad controlada**: Balance between quality and progress
- **ATDD**: Write functional tests first, then unit tests
- **Clean code**: Clear names, comments only when essential

### Imports

- **Standard library** first, then **third-party**, then **local**
- Always use absolute imports (no relative imports like `from ..models`)
- Group imports: stdlib, third-party, local
- Imports at the beginning of the file, not local to function, method or class, unless necessary

```python
# Correct
from typing import Tuple

import pytest
from django.forms.models import model_to_dict

from diario.models import Cuenta, CuentaInteractiva, Dia, Movimiento, SaldoDiario
```

### Formatting

- **Line length**: Max 120 characters (follow Django's style)
- **Indentation**: 4 spaces
- **Blank lines**: Two between top-level definitions, one between methods
- **No trailing whitespace**

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `FooterText`, `NavigationSettings`)
- **Functions/methods**: `snake_case` (e.g., `crear_sitio_con_homepage`)
- **Variables**: `snake_case` (e.g., `root_page`, `homepage`)
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: Prefix with `_` (e.g., `_get_hostname`)
- **Templates**: Lowercase with underscores (e.g., `footer.html`)
- **URL names**: Lowercase with hyphens (e.g., `wagtailadmin`)

### Django Patterns

- **Models**: Define in separate module under directory `models` per app. Add to `<app>/models/__init__.py`.
- **Templates**: Store in `<app>/templates/<app>/`
- **Static files**: Store in `static/<app>/`
- **Test files**: `tests.py` per app, or `test_*.py`

### Error Handling

- Use try/except with specific exceptions
- Always chain exceptions: `from exc`
- Raise descriptive `ImportError` messages
- Avoid bare `except:` clauses

### Test Organization

Follow this structure in tests:

1. **Functional tests**: Test from user perspective using templates
2. **Unit tests**: Test models, template tags, views


### Functional Tests (Selenium)

- Inherit from `FunctionalTestBase`
- Use explicit waits (`wait_for`, `wait_for_text`)
- Take screenshots on failure
- Clean up in `tearDownClass`

### Unit tests:
- Principalmente testean funciones o métodos.
- Los test para un método deben cumplir: 
  - qué valor debe devolver 
  - qué efectos colaterales debe tener
  - en qué casos debe lanzar una excepción
- Deben organizarse en clases o archivos según el método que estén testeando.


## Key Files

| Path                       | Description |
|----------------------------|-------------|
| `finper/settings.py`       | Main Django settings |
| `pytest.ini`               | pytest configuration |
