import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional
from contextlib import contextmanager
import io
from PIL import Image
from src.core.models import Ejercicio


def get_db_path() -> Path:
    """Retorna la ruta de la base de datos (junto al ejecutable o en el proyecto)."""
    import sys
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent.parent.parent
    return base_dir / "ejercicios.db"


@contextmanager
def get_connection():
    """Context manager para conexiones SQLite con WAL y PRAGMAs de alto rendimiento."""
    conn = sqlite3.connect(get_db_path(), timeout=15.0)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = -64000")  # 64MB de caché
    conn.execute("PRAGMA temp_store = MEMORY")
    try:
        yield conn
    finally:
        conn.close()


def generar_miniatura_bytes(imagen_bytes: bytes, max_size=(260, 180)) -> Optional[bytes]:
    """Genera una miniatura JPEG compacta (~2-8 KB) para evitar transferir BLOBs pesados a la UI."""
    if not imagen_bytes:
        return None
    try:
        with Image.open(io.BytesIO(imagen_bytes)) as img:
            if img.mode in ("RGBA", "LA", "P"):
                fondo = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                fondo.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = fondo
            elif img.mode != "RGB":
                img = img.convert("RGB")

            img.thumbnail(max_size, Image.Resampling.BILINEAR)
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=80, optimize=True)
            return out.getvalue()
    except Exception:
        return None


def init_database() -> None:
    """Inicializa la base de datos con tablas, índices y soporte para miniaturas ultrarrápidas."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS ejercicios
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      nombre TEXT,
                      dificultad TEXT,
                      imagen BLOB)''')

        # Migración segura: agregar columna miniatura si no existe
        c.execute("PRAGMA table_info(ejercicios)")
        columnas = [row[1] for row in c.fetchall()]
        if "miniatura" not in columnas:
            try:
                c.execute("ALTER TABLE ejercicios ADD COLUMN miniatura BLOB")
            except Exception:
                pass

        # Índice para acelerar filtros por dificultad y conteos instantáneos
        c.execute("CREATE INDEX IF NOT EXISTS idx_ejercicios_dificultad ON ejercicios(dificultad)")
        conn.commit()

        # Generar miniaturas en segundo plano para registros que no la tengan
        c.execute("SELECT id, imagen FROM ejercicios WHERE miniatura IS NULL AND imagen IS NOT NULL")
        sin_mini = c.fetchall()
        if sin_mini:
            actualizaciones = []
            for eid, img_bytes in sin_mini:
                mini = generar_miniatura_bytes(img_bytes)
                if mini:
                    actualizaciones.append((mini, eid))
            if actualizaciones:
                c.executemany("UPDATE ejercicios SET miniatura=? WHERE id=?", actualizaciones)
                conn.commit()


def agregar_ejercicio(nombre: str, dificultad: str, imagen_bytes: bytes) -> None:
    """Agrega un ejercicio generando automáticamente su miniatura para fluidez instantánea."""
    miniatura = generar_miniatura_bytes(imagen_bytes)
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO ejercicios (nombre, dificultad, imagen, miniatura) VALUES (?, ?, ?, ?)",
            (nombre, dificultad, imagen_bytes, miniatura),
        )
        conn.commit()


def agregar_ejercicios(ejercicios: List[Tuple[str, str, bytes]]) -> None:
    """Agrega varios ejercicios en una sola transacción eficiente con miniaturas precalculadas."""
    if not ejercicios:
        return
    datos = []
    for nombre, dificultad, img_bytes in ejercicios:
        mini = generar_miniatura_bytes(img_bytes)
        datos.append((nombre, dificultad, img_bytes, mini))

    with get_connection() as conn:
        c = conn.cursor()
        c.executemany(
            "INSERT INTO ejercicios (nombre, dificultad, imagen, miniatura) VALUES (?, ?, ?, ?)",
            datos,
        )
        conn.commit()


def obtener_ejercicios(cargar_imagenes: bool = False) -> List[Ejercicio]:
    """Obtiene todos los ejercicios. Por defecto no transfiere los BLOBs pesados a memoria."""
    with get_connection() as conn:
        c = conn.cursor()
        if cargar_imagenes:
            c.execute("SELECT id, nombre, dificultad, imagen, miniatura FROM ejercicios ORDER BY id DESC")
            rows = c.fetchall()
            return [
                Ejercicio(id=row[0], nombre=row[1], dificultad=row[2], imagen=row[3], miniatura=row[4])
                for row in rows
            ]
        else:
            c.execute("SELECT id, nombre, dificultad FROM ejercicios ORDER BY id DESC")
            rows = c.fetchall()
            return [
                Ejercicio(id=row[0], nombre=row[1], dificultad=row[2], imagen=b"", miniatura=None)
                for row in rows
            ]


def obtener_ejercicios_lista() -> List[Tuple[int, str, str]]:
    """Obtiene lista simple (id, nombre, dificultad) para listados rápidos."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, nombre, dificultad FROM ejercicios ORDER BY id DESC")
        return c.fetchall()


def obtener_miniatura(ejercicio_id: int) -> Optional[bytes]:
    """Obtiene la miniatura ligera de un ejercicio, generándola y guardándola si aún no existe."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT miniatura, imagen FROM ejercicios WHERE id=?", (ejercicio_id,))
        row = c.fetchone()
        if not row:
            return None
        miniatura, imagen = row
        if miniatura:
            return miniatura
        if imagen:
            mini = generar_miniatura_bytes(imagen)
            if mini:
                try:
                    c.execute("UPDATE ejercicios SET miniatura=? WHERE id=?", (mini, ejercicio_id))
                    conn.commit()
                except Exception:
                    pass
                return mini
            return imagen
        return None


def obtener_ejercicio_por_id(ejercicio_id: int) -> Optional[bytes]:
    """Obtiene la imagen original en alta resolución de un ejercicio por ID."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT imagen FROM ejercicios WHERE id=?", (ejercicio_id,))
        resultado = c.fetchone()
        return resultado[0] if resultado else None


def eliminar_ejercicio(ejercicio_id: int) -> None:
    """Elimina un ejercicio de la base de datos."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM ejercicios WHERE id=?", (ejercicio_id,))
        conn.commit()


def obtener_ejercicios_por_dificultad(dificultad: str, cantidad: int) -> List[int]:
    """Obtiene IDs de ejercicios aleatorios delegando la aleatoriedad directamente a SQLite."""
    if cantidad <= 0:
        return []
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id FROM ejercicios WHERE dificultad=? ORDER BY RANDOM() LIMIT ?",
            (dificultad, cantidad)
        )
        return [row[0] for row in c.fetchall()]


def contar_por_dificultad() -> dict:
    """Retorna conteo de ejercicios por dificultad optimizado con índice."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT dificultad, COUNT(*) FROM ejercicios GROUP BY dificultad")
        rows = c.fetchall()
        return {row[0]: row[1] for row in rows}
