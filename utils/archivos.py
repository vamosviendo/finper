from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path


def fijar_mtime(archivo: str | Path, mtime: datetime):
    if not isinstance(archivo, Path):
        archivo = Path(archivo)
    os.utime(
        archivo,
        (archivo.stat().st_ctime, datetime.timestamp(mtime))
    )
