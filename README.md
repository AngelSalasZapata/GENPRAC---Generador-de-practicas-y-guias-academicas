# Generador de Ejercicios PDF

Aplicación de escritorio para Windows que gestiona un banco de prácticas académicas y genera documentos PDF con ejercicios seleccionados por nivel de dificultad.

La aplicación activa está desarrollada con **Avalonia UI, C# y .NET 8**.

## Uso

1. Descargue el ejecutable desde la sección **Releases** de GitHub.
2. Ejecute `GeneradorEjerciciosAvalonia.exe` en Windows.
3. La aplicación no requiere instalar .NET: el ejecutable es autocontenido.

La base de datos `ejercicios.db` se guarda junto al ejecutable y se crea automáticamente si no existe. Para conservar los ejercicios al actualizar, no elimine ese archivo.

## Funcionalidades

- Generación aleatoria de PDFs por nivel de dificultad.
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

El ejecutable resultante se publica como archivo adjunto de un **GitHub Release**, no dentro del repositorio, para evitar incorporar binarios pesados al historial Git.

## Licencia de fuentes

Proyecto desarrollado por **Angel Fabiano Salas Zapata**.
