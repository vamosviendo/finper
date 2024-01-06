from datetime import date, datetime

from selenium.webdriver.common.by import By

from diario.models import Dia
from diario.utils.utils_saldo import saldo_general_historico
from utils.numeros import float_format


def test_movimientos_agrupados_por_dia(browser, conjunto_movimientos_varios_dias):
    # Dada una cantidad de movimientos distribuidos en 18 días, con algunos días
    # sin movimientos y otros con más de un movimiento
    movs = conjunto_movimientos_varios_dias
    fecha_ultimo_mov = Dia.ultime().fecha

    # En la sección de movimientos de la página principal aparecen los movimientos
    # de los últimos 7 días, ordenados por fecha descendente
    browser.ir_a_pag()
    dias = browser.esperar_elementos("class_div_dia")
    assert len(dias) == 7
    assert dias[0].esperar_elemento("class_span_fecha_dia", By.CLASS_NAME).text == fecha_ultimo_mov.strftime('%Y-%m-%d')

    # Los movimientos aparecen agrupados por día
    for dia in dias:
        movs_dia = dia.esperar_elementos("class_row_mov")
        str_fecha = dia.esperar_elemento("class_span_fecha_dia", By.CLASS_NAME).text
        fecha = datetime.strptime(str_fecha, "%Y-%m-%d")
        obj_dia = Dia.tomar(fecha=fecha)
        ult_mov = movs.filter(dia=obj_dia).last()
        saldo_ult_mov = saldo_general_historico(ult_mov)
        assert len(movs_dia) > 0

        # y cada día incluye el saldo histórico a esa fecha
        saldo_dia = dia.esperar_elemento("class_span_saldo_dia", By.CLASS_NAME).text
        assert saldo_dia == float_format(saldo_ult_mov)

    # Si un día no tiene movimientos, no aparece
    # y ese día no se computa a los efectos de completar los 7 días mostrados

    # Al final de la lista de días y movimientos, aparece una barra de navegación
    # que permite recorrer los movimientos anteriores y volver a los posteriores

    # Si pulsamos en un movimiento, somos dirigidos a la página de detalles
    # del movimiento, con saldos y capitales históricos al momento del movimiento

    # Si pulsamos en una fecha, somos dirigidos a la página de detalles del
    # último movimiento del día
    ...
