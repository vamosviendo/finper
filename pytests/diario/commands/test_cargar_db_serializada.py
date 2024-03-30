from pathlib import Path

from django.core.management import call_command

from diario.models import Titular, Moneda
from finper import settings


def test_vacia_la_base_de_datos_antes_de_cargar_datos_nuevos(mocker, vaciar_db):
    mock_unlink = mocker.patch("pathlib.Path.unlink", autospec=True)
    call_command("cargar_db_serializada")
    mock_unlink.assert_called_once_with(Path(settings.BASE_DIR / "db.sqlite3"), missing_ok=True)


def test_carga_todos_los_titulares_en_la_base_de_datos(titular, otro_titular, db_serializada, vaciar_db):
    tits = db_serializada.filter_by_model("diario.titular")
    call_command("cargar_db_serializada")
    for tit in tits:
        Titular.tomar(titname=tit.fields["titname"])


def test_carga_todas_las_monedas_en_la_base_de_datos(peso, dolar, euro, db_serializada, vaciar_db):
    monedas = db_serializada.filter_by_model("diario.moneda")
    call_command("cargar_db_serializada")
    for moneda in monedas:
        Moneda.tomar(monname=moneda.fields["monname"])
