from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Ejercicio:
    id: int
    nombre: str
    dificultad: str
    imagen: bytes = b""
    miniatura: Optional[bytes] = None


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
    espacio_cm: float = 0.0


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
    "Básico": "#059669",
    "Intermedio": "#0284c7",
    "Difícil": "#d97706"
}
DIFICULTAD_FONDOS = {
    "Básico": "#d1fae5",
    "Intermedio": "#e0f2fe",
    "Difícil": "#fef3c7"
}