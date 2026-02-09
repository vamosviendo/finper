from datetime import date

import pytest

from utils.tiempo import str2date


def test_si_recibe_fecha_separada_por_guiones_devuelve_fecha():
    assert str2date("2026-05-02") == date(2026,5,2)


def test_si_recibe_fecha_no_separada_por_guiones_devuelve_fecha():
    assert str2date("20260502") == date(2026,5,2)


def test_si_recibe_cualquier_otra_cosa_da_error():
    with pytest.raises(ValueError):
        str2date("2026hh44")
