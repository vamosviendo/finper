from __future__ import annotations


# TODO: Pasar a vvmodel. Cuando lo pasemos, agregar argumento "omitir" a MiModel.cleean_save()
class Cleaner:
    """ Recorre y ejecuta todos los métodos que se agreguen la subclase,
        excepto los indicados en exclude o los marcados como internos con _
    """
    def __init__(self, exclude: list[str] | None = None):
        self.exclude = exclude or []

    def procesar(self):
        for nombre_metodo in self.__class__.__dict__:
            if not nombre_metodo.startswith("_") and nombre_metodo != "procesar" and nombre_metodo not in self.exclude:
                metodo = getattr(self, nombre_metodo, None)
                if callable(metodo):
                    metodo()
