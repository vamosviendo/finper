import json
from pathlib import Path
from typing import Any, TextIO

import pytest


@pytest.fixture
def lista_diccionarios() -> list[dict[Any: Any]]:
    return [
        {'uno': 1, 'dos': '2', 'tres': 3}
    ]


@pytest.fixture
def archivo_vacio_ro() -> TextIO:
    path_archivo = Path('archivo_vacio.txt')
    path_archivo.touch()
    with open('archivo_vacio.txt', 'r') as archivo:
        yield archivo
    path_archivo.unlink()


@pytest.fixture
def archivo_json(lista_diccionarios: list[dict[Any: Any]]) -> TextIO:
    with open('archivo.json', 'w') as archivo:
        json.dump(lista_diccionarios, archivo)
        archivo.close()
    with open('archivo.json', 'r') as archivo:
        yield archivo
    Path('archivo.json').unlink()
