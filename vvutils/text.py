from django.utils.text import slugify


def mi_slugify(value, reemplazo='', maximo=0, allow_unicode=False):
    """ Modificación de django.utils.text.slugify() que elimina espacios en
        blanco o los reemplaza por un carácter dado y permite acotar slug
        a una longitud máxima.
    """
    # Eliminar espacios en blanco en vez de reemplazarlos por guiones
    slug = slugify(value.replace(' ', reemplazo), allow_unicode=allow_unicode)

    # Si se proporciona una longitud máxima, acotar longitud.
    if maximo and len(slug) > maximo:
        slug = slug[:maximo]

    return slug
