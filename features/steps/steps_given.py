""" Las implementaciones deben ir de lo más particular a lo más general.
    Por ejemplo:
        @when('agrego una cuenta con nombre "{nombre}" y slug "{slug}"')
        @when('agrego una cuenta con nombre "{nombre}"')
        @when('agrego una cuenta')
"""
from behave import given

from diario.models import Cuenta, Movimiento, Titular
from helpers import table_to_str


@given('{n} movimientos con los siguientes valores')
def hay_n_movimientos(context, n):
    for fila in context.table:
        slug_entrada = fila.get('cta_entrada')
        slug_salida = fila.get('cta_salida')
        cta_entrada = cta_salida = None

        if slug_entrada:
            cta_entrada = Cuenta.tomar(slug=slug_entrada)
        if slug_salida:
            cta_salida = Cuenta.tomar(slug=slug_salida)

        Movimiento.crear(
            concepto=fila['concepto'],
            importe=fila['importe'],
            cta_entrada=cta_entrada,
            cta_salida=cta_salida,
        )


@given('la cuenta "{nombre}" dividida en subcuentas')
def cuenta_dividida(context, nombre):
    cta = Cuenta.tomar(nombre=nombre.lower())
    subcuentas = list()
    for fila in context.table:
        subcuentas.append(dict(
                nombre=fila['nombre'],
                slug=fila['slug'],
                saldo=fila['saldo'] or None
        ))
    cta.dividir_entre(*subcuentas)


@given('movimientos con estos valores')
def hay_n_movimientos(context):
    for fila in context.table:
        ce = cs = None
        if fila.get('cta_entrada') is not None:
            ce = Cuenta.tomar(slug=fila.get('cta_entrada'))
        if fila.get('cta_salida') is not None:
            cs = Cuenta.tomar(slug=fila.get('cta_salida'))
        Movimiento.crear(
            concepto=fila['concepto'],
            importe=fila['importe'],
            cta_entrada=ce,
            cta_salida=cs,
        )


@given('un movimiento con los siguientes valores')
def hay_un_movimiento(context):
    context.execute_steps(
        'Dados 1 movimientos con los siguientes valores\n ' +
        table_to_str(context.table)
    )


@given('un error de {cantidad} pesos en el saldo de la cuenta "{nombre}"')
def hay_un_error_en_el_saldo(context, cantidad, nombre):
    cta = Cuenta.tomar(nombre=nombre.lower())
    cta.saldo += float(cantidad)
    cta.save()
    context.test.assertNotEqual(cta.saldo, cta.total_movs())


@given('{n} cuentas con los siguientes valores')
def hay_n_cuentas(context, n):
    for fila in context.table:
        Cuenta.crear(
            fila['nombre'], fila['slug'],
            titular=Titular.tomar_o_nada(titname=fila.get('titular')),
            saldo=fila.get('saldo', 0.0)
        )


@given('una cuenta con los siguientes valores')
def hay_una_cuenta(context):
    context.execute_steps(
        'Dadas 1 cuentas con los siguientes valores\n ' +
        table_to_str(context.table)
    )


@given('{n} titulares con los siguientes valores')
def hay_n_titulares(context, n):
    for fila in context.table:
        Titular.crear(
            titname=fila['titname'],
            nombre=fila.get('nombre') or fila['titname']
        )


@given('un titular con los siguientes valores')
def hay_un_titular(context):
    context.execute_steps(
        'Dados 1 titulares con los siguientes valores\n' +
        table_to_str(context.table)
    )


@given('un titular')
def hay_un_titular(context):
    context.execute_steps(
        """Dado un titular con los siguientes valores:
               | titname | nombre     |
               | tito    | Tito Gómez |
        """
    )


@given('dos titulares')
def hay_dos_titulares(context):
    context.execute_steps(
        """Dados 2 titulares con los siguientes valores:
            | titname | nombre      |
            | tito    | Tito Gómez  |
            | juan    | Juan Juánez |
        """
    )


@given('una cuenta')
def hay_una_cuenta(context):
    context.execute_steps(
        'Dada una cuenta con los siguientes valores\n'
        '| nombre   | slug |\n'
        '| Efectivo | e    |'
    )


@given('dos cuentas')
def hay_dos_cuentas(context):
    context.execute_steps(
        '''Dadas 2 cuentas con los siguientes valores
            | nombre   | slug |
            | Efectivo | e    |
            | Banco    | b    |
        '''
    )


@given('tres cuentas')
def hay_tres_cuentas(context):
    context.execute_steps(
        '''Dadas 2 cuentas con los siguientes valores
            | nombre   | slug |
            | Efectivo | e    |
            | Banco    | b    |
            | Caja     | c    |
        '''
    )


@given('cuatro cuentas')
def hay_cuatro_cuentas(context):
    context.execute_steps(
        '''Dadas 2 cuentas con los siguientes valores
            | nombre   | slug |
            | Efectivo | e    |
            | Banco    | b    |
            | Caja     | c    |
            | Crédito  | r    |
        '''
    )


@given('una cuenta acumulativa')
def hay_una_cuenta_acumulativa(context):
    context.execute_steps(
        'Dada una cuenta con los siguientes valores\n'
        '| nombre               | slug  |\n'
        '| Efectivo Acumulativa | ea    |\n'
        ' Y la cuenta "Efectivo Acumulativa" dividida en subcuentas\n'
        '| nombre     | slug | saldo |\n'
        '| efect_sub1 | es1  | 0.0   |\n'
        '| efect_sub2 | es2  | 0.0   |'
    )
