import streamlit as st
from fpdf import FPDF
from datetime import datetime
import sqlite3
import random
import io
from PIL import Image
import os

# ==================== BASE DE DATOS ====================
def init_database():
    """Inicializa la base de datos de ejercicios"""
    conn = sqlite3.connect('ejercicios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ejercicios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT,
                  dificultad TEXT,
                  imagen BLOB)''')
    conn.commit()
    conn.close()

def agregar_ejercicio(nombre, dificultad, imagen_bytes):
    """Agrega un ejercicio a la base de datos"""
    conn = sqlite3.connect('ejercicios.db')
    c = conn.cursor()
    c.execute("INSERT INTO ejercicios (nombre, dificultad, imagen) VALUES (?, ?, ?)",
              (nombre, dificultad, imagen_bytes))
    conn.commit()
    conn.close()

def obtener_ejercicios():
    """Obtiene todos los ejercicios de la base de datos"""
    conn = sqlite3.connect('ejercicios.db')
    c = conn.cursor()
    c.execute("SELECT id, nombre, dificultad FROM ejercicios")
    ejercicios = c.fetchall()
    conn.close()
    return ejercicios

def obtener_ejercicio_por_id(ejercicio_id):
    """Obtiene un ejercicio específico por ID"""
    conn = sqlite3.connect('ejercicios.db')
    c = conn.cursor()
    c.execute("SELECT imagen FROM ejercicios WHERE id=?", (ejercicio_id,))
    resultado = c.fetchone()
    conn.close()
    return resultado[0] if resultado else None

def eliminar_ejercicio(ejercicio_id):
    """Elimina un ejercicio de la base de datos"""
    conn = sqlite3.connect('ejercicios.db')
    c = conn.cursor()
    c.execute("DELETE FROM ejercicios WHERE id=?", (ejercicio_id,))
    conn.commit()
    conn.close()

def obtener_ejercicios_por_dificultad(dificultad, cantidad):
    """Obtiene ejercicios aleatorios de una dificultad específica"""
    conn = sqlite3.connect('ejercicios.db')
    c = conn.cursor()
    c.execute("SELECT id FROM ejercicios WHERE dificultad=?", (dificultad,))
    todos = [row[0] for row in c.fetchall()]
    conn.close()
    
    if len(todos) < cantidad:
        st.warning(f"⚠️ Solo hay {len(todos)} ejercicios de nivel {dificultad}, se necesitan {cantidad}")
        return todos
    
    return random.sample(todos, cantidad)

# ==================== GENERADOR DE PDF ====================
class PDFEjercicios(FPDF):
    def header(self):
        # Título principal
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Guía de Prácticas Académicas', 0, 1, 'C')

        # Autor
        self.set_font('Arial', '', 10)
        self.cell(0, 6, 'Por: Angel Fabiano Salas Zapata', 0, 1, 'C')

        
        # Espacio después del encabezado
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf_ejercicios(ejercicios_ids, filename="ejercicios.pdf"):
    """Genera un PDF con los ejercicios en 2 columnas"""
    pdf = PDFEjercicios('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)  # Desactivar auto page break para control manual
    
    # Configuración de columnas
    col_width = 90  # Ancho de cada columna
    col_spacing = 10  # Espacio entre columnas
    img_height = 60  # Altura de cada imagen
    margin_left = 10
    margin_top = 35  # Margen superior después del header
    margin_bottom = 20  # Margen inferior antes del footer
    
    x_positions = [margin_left, margin_left + col_width + col_spacing]
    current_col = 0
    current_y = margin_top
    
    for idx, ej_id in enumerate(ejercicios_ids):
        imagen_bytes = obtener_ejercicio_por_id(ej_id)
        if not imagen_bytes:
            continue
        
        # Guardar imagen temporalmente
        temp_img_path = f"temp_img_{ej_id}.png"
        with open(temp_img_path, 'wb') as f:
            f.write(imagen_bytes)
        
        # Calcular posición
        x_pos = x_positions[current_col]
        
        # Verificar si necesitamos nueva página
        espacio_necesario = img_height + 10  # Espacio para imagen + número
        if current_y + espacio_necesario > pdf.h - margin_bottom:
            # Crear nueva página
            pdf.add_page()
            current_y = margin_top
            current_col = 0
            x_pos = x_positions[current_col]
        
        # Número de ejercicio
        pdf.set_xy(x_pos, current_y)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(col_width, 5, f'Ejercicio {idx + 1}', 0, 0, 'L')
        
        # Imagen del ejercicio
        pdf.image(temp_img_path, x=x_pos, y=current_y + 5, w=col_width)
        
        # Limpiar archivo temporal
        os.remove(temp_img_path)
        
        # Avanzar a siguiente posición
        if current_col == 0:
            # Pasar a columna derecha
            current_col = 1
        else:
            # Volver a columna izquierda y bajar una fila
            current_col = 0
            current_y += img_height + 10
    
    pdf.output(filename)
    return filename

# ==================== INTERFAZ STREAMLIT ====================
def main():
    st.set_page_config(page_title="Generador de Ejercicios PDF", layout="wide")
    
    # Inicializar base de datos
    init_database()
    
    st.title("📝 Generador de PDFs con Ejercicios Aleatorios")
    
    # Pestañas principales
    tab1, tab2, tab3 = st.tabs(["🎲 Generar PDF", "📚 Gestionar Banco", "📊 Estadísticas"])
    
    # ==================== TAB 1: GENERAR PDF ====================
    with tab1:
        st.header("Generar Documento Aleatorio")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Configuración de Ejercicios")
            
            basicos = st.number_input("Ejercicios Básicos", min_value=0, max_value=60, value=30)
            intermedios = st.number_input("Ejercicios Intermedios", min_value=0, max_value=60, value=20)
            dificiles = st.number_input("Ejercicios Difíciles", min_value=0, max_value=60, value=10)
            
            total = basicos + intermedios + dificiles
            st.info(f"📊 Total de ejercicios: **{total}**")
            
            if st.button("🎲 Generar PDF Aleatorio", type="primary", use_container_width=True):
                with st.spinner("Generando PDF..."):
                    # Obtener ejercicios aleatorios por dificultad
                    ejercicios_basicos = obtener_ejercicios_por_dificultad("Básico", basicos)
                    ejercicios_intermedios = obtener_ejercicios_por_dificultad("Intermedio", intermedios)
                    ejercicios_dificiles = obtener_ejercicios_por_dificultad("Difícil", dificiles)
                    
                    # Combinar y mezclar
                    todos_ejercicios = ejercicios_basicos + ejercicios_intermedios + ejercicios_dificiles
                    random.shuffle(todos_ejercicios)
                    
                    if len(todos_ejercicios) < total:
                        st.error(f"❌ No hay suficientes ejercicios. Disponibles: {len(todos_ejercicios)}, Necesarios: {total}")
                    else:
                        # Generar PDF
                        pdf_filename = generar_pdf_ejercicios(todos_ejercicios)
                        
                        st.success("✅ ¡PDF generado exitosamente!")
                        
                        # Botón de descarga
                        with open(pdf_filename, "rb") as pdf_file:
                            st.download_button(
                                label="📥 Descargar PDF",
                                data=pdf_file.read(),
                                file_name="ejercicios_generados.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
        
        with col2:
            st.subheader("Vista Previa")
            ejercicios = obtener_ejercicios()
            
            if ejercicios:
                # Mostrar muestra aleatoria
                muestra = random.sample(ejercicios, min(3, len(ejercicios)))
                for ej_id, nombre, dificultad in muestra:
                    with st.expander(f"📄 {nombre} ({dificultad})"):
                        imagen_bytes = obtener_ejercicio_por_id(ej_id)
                        if imagen_bytes:
                            st.image(imagen_bytes, use_container_width=True)
            else:
                st.info("No hay ejercicios para mostrar")
    
    # ==================== TAB 2: GESTIONAR BANCO ====================
    with tab2:
        st.header("Gestión del Banco de Ejercicios")
        
        col1, col2 = st.columns(2)
        
        # Agregar ejercicios
        with col1:
            st.subheader("➕ Agregar Ejercicio")
            
            nombre = st.text_input("Nombre del ejercicio", key="nombre_ejercicio")
            dificultad = st.selectbox("Dificultad", ["Básico", "Intermedio", "Difícil"], key="dificultad")
            imagen = st.file_uploader("Imagen del ejercicio", type=["png", "jpg", "jpeg"], key="imagen_upload")
            
            if st.button("Agregar al Banco", use_container_width=True):
                if nombre and imagen:
                    imagen_bytes = imagen.read()
                    agregar_ejercicio(nombre, dificultad, imagen_bytes)
                    st.success(f"✅ Ejercicio '{nombre}' agregado correctamente")
                    st.rerun()
                else:
                    st.error("❌ Por favor completa todos los campos")
        
        # Listar y eliminar ejercicios
        with col2:
            st.subheader("🗂️ Ejercicios Actuales")
            
            ejercicios = obtener_ejercicios()
            
            if ejercicios:
                for ej_id, nombre, dificultad in ejercicios:
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.text(f"📄 {nombre} - {dificultad}")
                    with col_b:
                        if st.button("🗑️", key=f"delete_{ej_id}"):
                            eliminar_ejercicio(ej_id)
                            st.rerun()
            else:
                st.info("No hay ejercicios en el banco")
    
    # ==================== TAB 3: ESTADÍSTICAS ====================
    with tab3:
        st.header("📊 Estadísticas del Banco")
        
        ejercicios = obtener_ejercicios()
        
        if ejercicios:
            # Contar por dificultad
            stats = {"Básico": 0, "Intermedio": 0, "Difícil": 0}
            for _, _, dificultad in ejercicios:
                stats[dificultad] += 1
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Ejercicios", len(ejercicios))
            with col2:
                st.metric("Básicos", stats["Básico"], delta="✅" if stats["Básico"] >= 30 else "⚠️")
            with col3:
                st.metric("Intermedios", stats["Intermedio"], delta="✅" if stats["Intermedio"] >= 20 else "⚠️")
            with col4:
                st.metric("Difíciles", stats["Difícil"], delta="✅" if stats["Difícil"] >= 10 else "⚠️")
            
            st.divider()
            
            # Gráfico simple
            st.subheader("Distribución por Dificultad")
            st.bar_chart(stats)
        else:
            st.info("No hay ejercicios para mostrar estadísticas")

if __name__ == "__main__":
    main()