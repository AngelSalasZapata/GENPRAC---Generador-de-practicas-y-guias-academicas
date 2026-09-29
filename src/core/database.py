import sqlite3
import random
from pathlib import Path
from typing import List, Tuple, Optional
from src.core.models import Ejercicio


def get_db_path() -> Path:
    """Retorna la ruta de la base de datos (junto al ejecutable o en APPDATA)"""
    import sys
    if getattr(sys, 'frozen', False):
        # Ejecutando como exe compilado
        base_dir = Path(sys.executable).parent
    else:
        # Ejecutando como script
        base_dir = Path(__file__).parent.parent.parent
    return base_dir / "ejercicios.db"


def init_database() -> None:
    """Inicializa la base de datos de ejercicios"""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ejercicios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT,
                  dificultad TEXT,
                  imagen BLOB)''')
    conn.commit()
    conn.close()


def agregar_ejercicio(nombre: str, dificultad: str, imagen_bytes: bytes) -> None:
    """Agrega un ejercicio a la base de datos"""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("INSERT INTO ejercicios (nombre, dificultad, imagen) VALUES (?, ?, ?)",
              (nombre, dificultad, imagen_bytes))
    conn.commit()
    conn.close()


def obtener_ejercicios() -> List[Ejercicio]:
    """Obtiene todos los ejercicios de la base de datos"""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("SELECT id, nombre, dificultad, imagen FROM ejercicios")
    rows = c.fetchall()
    conn.close()
    return [Ejercicio(id=row[0], nombre=row[1], dificultad=row[2], imagen=row[3]) for row in rows]


def obtener_ejercicios_lista() -> List[Tuple[int, str, str]]:
    """Obtiene lista simple (id, nombre, dificultad) para listados"""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("SELECT id, nombre, dificultad FROM ejercicios")
    rows = c.fetchall()
    conn.close()
    return rows


def obtener_ejercicio_por_id(ejercicio_id: int) -> Optional[bytes]:
    """Obtiene la imagen de un ejercicio específico por ID"""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("SELECT imagen FROM ejercicios WHERE id=?", (ejercicio_id,))
    resultado = c.fetchone()
    conn.close()
    return resultado[0] if resultado else None


def eliminar_ejercicio(ejercicio_id: int) -> None:
    """Elimina un ejercicio de la base de datos"""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("DELETE FROM ejercicios WHERE id=?", (ejercicio_id,))
    conn.commit()
    conn.close()


def obtener_ejercicios_por_dificultad(dificultad: str, cantidad: int) -> List[int]:
    """Obtiene IDs de ejercicios aleatorios de una dificultad específica"""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("SELECT id FROM ejercicios WHERE dificultad=?", (dificultad,))
    todos = [row[0] for row in c.fetchall()]
    conn.close()

    if len(todos) < cantidad:
        return todos

    return random.sample(todos, cantidad)


def contar_por_dificultad() -> dict:
    """Retorna conteo de ejercicios por dificultad"""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("SELECT dificultad, COUNT(*) FROM ejercicios GROUP BY dificultad")
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}