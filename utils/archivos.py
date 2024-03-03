from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import TextIO


def es_json_valido(archivo: TextIO) -> bool:
    try:
        json.load(archivo)
        return True
    except json.JSONDecodeError:
        return False


def fijar_mtime(archivo: str | Path, mtime: datetime):
    if not isinstance(archivo, Path):
        archivo = Path(archivo)
    os.utime(
        archivo,
        (archivo.stat().st_ctime, datetime.timestamp(mtime))
    )
