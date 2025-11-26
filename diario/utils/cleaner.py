from __future__ import annotations


# TODO: Pasar a vvmodel
class Cleaner:
    """ Recorre y ejecuta todos los métodos que se agreguen la subclase,
        excepto los indicados en exclude o los marcados como internos con _
    """
    def __init__(self, exclude: list[str] | None = None):
        self.exclude = exclude or []

    def procesar(self):
        for nombre_metodo in dir(self):
            if (callable(getattr(self, nombre_metodo))) and \
                    not nombre_metodo.startswith("_") and \
                    nombre_metodo != "procesar" and nombre_metodo not in self.exclude:
                metodo = getattr(self, nombre_metodo)
                metodo()
