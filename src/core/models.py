from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Ejercicio:
    id: int
    nombre: str
    dificultad: str
    imagen: bytes


@dataclass
class ConfiguracionPDF:
    basicos: int = 30
    intermedios: int = 20
    dificiles: int = 10

    @property
    def total(self) -> int:
        return self.basicos + self.intermedios + self.dificiles


@dataclass
class ConfiguracionDocumento:
    """Datos personalizables del documento PDF generado."""
    titulo: str = "Guía de Prácticas Académicas"
    autor: str = "Angel Fabiano Salas Zapata"
    etiqueta: str = "Ejercicio"


@dataclass
class EstadisticasBanco:
    total: int
    basicos: int
    intermedios: int
    dificiles: int

    @property
    def esta_completo(self) -> bool:
        return self.basicos >= 30 and self.intermedios >= 20 and self.dificiles >= 10


DIFICULTADES = ["Básico", "Intermedio", "Difícil"]
ETIQUETAS_DOCUMENTO = ["Ejercicio", "Enunciado", "Problema", "Pregunta", "Actividad"]
DIFICULTAD_COLORES = {
    "Básico": "#27ae60",
    "Intermedio": "#f39c12",
    "Difícil": "#e74c3c"
}
DIFICULTAD_FONDOS = {
    "Básico": "#e8f8f0",
    "Intermedio": "#fef5e7",
    "Difícil": "#fdedec"
}