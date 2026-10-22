# AGENTS.md - Development Guidelines for wlili

Este archivo complementa el `AGENTS.md` global
(`~/.config/opencode/AGENTS.md`). Aquí vive sólo lo específico del
proyecto. Ante conflicto, este archivo tiene prioridad sobre el global.

## Project Overview

- **Type**: Django Accounting system (sistema contable)
- **Python**: 3.x
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Testing**: pytest + Selenium (functional tests)

## Build / Lint / Test Commands

### Django Management

```bash
python src/manage.py runserver
python src/manage.py migrate
python src/manage.py makemigrations
python src/manage.py collectstatic --noinput
```

### Running Tests

```bash
pytest                                                            # all
pytest base/tests.py                                              # single file
pytest base/tests.py::FooterFunctionalTests                       # single class
pytest base/tests.py::FooterFunctionalTests::test_footer_renders_without_error
pytest -k "not FunctionalTest"                                    # unit/integration only
pytest functional_tests/                                          # functional only
pytest -v
pytest --reuse-db --no-migrateci
```

Buscar estos y otros comandos en Makefile

## Django Patterns del proyecto

- **Models**: definir en módulo separado bajo el directorio `models` de
  cada app. Agregar a `<app>/models/__init__.py`.
- **Test files**: `tests.py` por app, o `test_*.py`. **Override del global**:
  en este proyecto los tests viven dentro de las apps, no en un `tests/`
  raíz.

## Functional Tests (Selenium)

- Heredan de `FunctionalTestBase`.
- Usan waits explícitos (`wait_for`, `wait_for_text`).
- Sacan screenshot al fallar.
- Hacen cleanup en `tearDownClass`.

## Key Files

| Path                  | Description           |
|-----------------------|-----------------------|
| `finper/settings.py`  | Main Django settings  |
| `pytest.ini`          | pytest configuration  |

## Procedimientos particulares

La forma correcta de crear una cuenta acumulativa es crearla como cuenta
interactiva y luego ejecutar el método `CuentaInteractiva.dividir_entre`
(o bien `CuentaInteractiva.dividir_y_actualizar` si queremos que devuelva
la cuenta transformada) para convertirla en acumulativa con subcuentas.

Ejemplo:

```python
def crear_cuenta_acumulativa(cuenta: CuentaInteractiva) -> Cuenta:
    return cuenta.dividir_y_actualizar([subcuenta1, sc1, 0], [subcuenta2, sc3, 0])
```