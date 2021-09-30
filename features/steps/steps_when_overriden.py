from features.steps.helpers import overrides


@overrides('cliqueo en el botón "{texto}"', 'when')
def cliquear_en_el_boton(context, texto):
    context.execute_steps(
        f'Cuando cliqueo en el botón de contenido "{texto}"'
    )
