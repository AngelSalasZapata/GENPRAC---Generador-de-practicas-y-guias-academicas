# Generador de Ejercicios PDF

Aplicación de escritorio para Windows que gestiona un banco de prácticas académicas y genera documentos PDF con ejercicios seleccionados por nivel de dificultad.

La aplicación activa está desarrollada con **Avalonia UI, C# y .NET 8**.

## Uso

1. Descargue el archivo ZIP de la versión más reciente desde la sección **Releases** de GitHub.
2. Extraiga el ZIP completo en una carpeta de Windows.
3. Ejecute `GeneradorEjerciciosAvalonia.exe` sin moverlo fuera de esa carpeta.
4. La aplicación no requiere instalar .NET: la distribución es autocontenida.

La base de datos `ejercicios.db` se guarda junto al ejecutable y se crea automáticamente si no existe. Para conservar los ejercicios al actualizar, no elimine ese archivo.

## Funcionalidades

- Generación aleatoria de PDFs por nivel de dificultad.
- Vista previa en tiempo real del documento y de los ejercicios seleccionados.
- Configuración opcional de un alto uniforme para todas las imágenes, expresado en centímetros.
- Banco de ejercicios con búsqueda, filtros y paginación.
- Carga individual y masiva de imágenes.
- Miniaturas almacenadas en SQLite.
- Vista previa y generación de documentos con QuestPDF.

## Estructura

```text
GENPRAC/
├── GeneradorEjerciciosAvalonia/       # Código fuente de la aplicación
│   ├── Models/                         # Entidades y constantes
│   ├── Services/                       # SQLite, PDF e imágenes
│   ├── ViewModels/                     # Lógica MVVM
│   └── Views/                          # Vistas AXAML
├── ejercicios.db                       # Base de datos de desarrollo opcional
└── README.md
```

## Desarrollo

Requisitos: **.NET 8 SDK**.

```bash
cd GeneradorEjerciciosAvalonia
dotnet run
```

Para generar la distribución autocontenida de Windows x64:

```bash
dotnet publish GeneradorEjerciciosAvalonia/GeneradorEjerciciosAvalonia.csproj \
  -c Release -r win-x64 --self-contained true \
  -p:PublishSingleFile=true -o dist-avalonia
```

La carpeta publicada se distribuye como un ZIP adjunto de un **GitHub Release**, no dentro del repositorio, para evitar incorporar binarios pesados al historial Git. Debe conservarse la estructura completa del ZIP porque incluye las bibliotecas nativas necesarias para Avalonia, SQLite y QuestPDF.

## Licencia de fuentes

Proyecto desarrollado por **Angel Fabiano Salas Zapata**.
