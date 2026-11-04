using System;
using System.Collections.ObjectModel;
using System.Globalization;
using System.Threading.Tasks;
using Avalonia.Media.Imaging;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using GeneradorEjerciciosAvalonia.Models;
using GeneradorEjerciciosAvalonia.Services;

namespace GeneradorEjerciciosAvalonia.ViewModels;

public partial class GenerarViewModel : ViewModelBase
{
    private const int Minimo = 0;
    private const int Maximo = 60;

    private readonly MainViewModel _main;

    [ObservableProperty] private bool _esVisible;
    [ObservableProperty] private int _basicos = 30;
    [ObservableProperty] private int _intermedios = 20;
    [ObservableProperty] private int _dificiles = 10;
    [ObservableProperty] private string _titulo = ConfiguracionDocumento.TituloPorDefecto;
    [ObservableProperty] private string _autor = ConfiguracionDocumento.AutorPorDefecto;
    [ObservableProperty] private string _etiqueta = ConfiguracionDocumento.EtiquetaPorDefecto;
    [ObservableProperty] private bool _agregarEspacio;
    [ObservableProperty] private string _espacioTexto = "2.0";
    [ObservableProperty] private bool _imagenesMismoTamano;
    [ObservableProperty] private string _tamanoImagenTexto = "5.0";

    public ObservableCollection<VistaPreviaEjercicioViewModel> VistaPrevia { get; } = new();
    public bool HayVistaPrevia => VistaPrevia.Count > 0;
    public string TextoVistaPrevia => HayVistaPrevia
        ? "Vista previa · se muestran ejercicios del banco"
        : "No hay ejercicios con imágenes para mostrar";

    public string[] Etiquetas => Constantes.EtiquetasDocumento;

    public string TotalTexto => $"📊 Total de ejercicios: {Basicos + Intermedios + Dificiles}";

    public GenerarViewModel(MainViewModel main)
    {
        _main = main;
        ActualizarVistaPrevia();
    }

    partial void OnBasicosChanged(int value) { OnPropertyChanged(nameof(TotalTexto)); ActualizarVistaPrevia(); }
    partial void OnIntermediosChanged(int value) { OnPropertyChanged(nameof(TotalTexto)); ActualizarVistaPrevia(); }
    partial void OnDificilesChanged(int value) { OnPropertyChanged(nameof(TotalTexto)); ActualizarVistaPrevia(); }
    partial void OnTituloChanged(string value) => ActualizarVistaPrevia();
    partial void OnAutorChanged(string value) => ActualizarVistaPrevia();
    partial void OnEtiquetaChanged(string value) => ActualizarVistaPrevia();
    partial void OnAgregarEspacioChanged(bool value) => ActualizarVistaPrevia();
    partial void OnEspacioTextoChanged(string value) => ActualizarVistaPrevia();
    partial void OnImagenesMismoTamanoChanged(bool value) => ActualizarVistaPrevia();
    partial void OnTamanoImagenTextoChanged(string value) => ActualizarVistaPrevia();

    [RelayCommand] private void IncrementarBasicos() => Basicos = Math.Min(Maximo, Basicos + 1);
    [RelayCommand] private void DecrementarBasicos() => Basicos = Math.Max(Minimo, Basicos - 1);
    [RelayCommand] private void IncrementarIntermedios() => Intermedios = Math.Min(Maximo, Intermedios + 1);
    [RelayCommand] private void DecrementarIntermedios() => Intermedios = Math.Max(Minimo, Intermedios - 1);
    [RelayCommand] private void IncrementarDificiles() => Dificiles = Math.Min(Maximo, Dificiles + 1);
    [RelayCommand] private void DecrementarDificiles() => Dificiles = Math.Max(Minimo, Dificiles - 1);

    [RelayCommand]
    private Task Generar() => _main.GenerarPdfAsync(this);

    public ConfiguracionPdf ObtenerConfig() => new()
    {
        Basicos = Basicos,
        Intermedios = Intermedios,
        Dificiles = Dificiles,
    };

    public ConfiguracionDocumento ObtenerDocumento()
    {
        var espacio = 0.0;
        if (AgregarEspacio)
        {
            var texto = (EspacioTexto ?? string.Empty).Trim().Replace(',', '.');
            if (!double.TryParse(texto, NumberStyles.Float, CultureInfo.InvariantCulture, out espacio))
            {
                espacio = 0.0;
            }
            espacio = Math.Max(0.0, espacio);
        }

        return new ConfiguracionDocumento
        {
            Titulo = string.IsNullOrWhiteSpace(Titulo) ? ConfiguracionDocumento.TituloPorDefecto : Titulo.Trim(),
            Autor = string.IsNullOrWhiteSpace(Autor) ? ConfiguracionDocumento.AutorPorDefecto : Autor.Trim(),
            Etiqueta = string.IsNullOrWhiteSpace(Etiqueta) ? ConfiguracionDocumento.EtiquetaPorDefecto : Etiqueta.Trim(),
            EspacioCm = espacio,
            ImagenesMismoTamano = ImagenesMismoTamano,
            TamanoImagenCm = ObtenerTamanoImagen(),
        };
    }

    private double ObtenerTamanoImagen()
    {
        var texto = (TamanoImagenTexto ?? string.Empty).Trim().Replace(',', '.');
        return double.TryParse(texto, NumberStyles.Float, CultureInfo.InvariantCulture, out var tamano)
            ? Math.Max(0.1, tamano)
            : 5.0;
    }

    private void ActualizarVistaPrevia()
    {
        foreach (var item in VistaPrevia) item.Dispose();
        VistaPrevia.Clear();

        var restantes = 16;
        var grupos = new[]
        {
            ("Básico", Basicos),
            ("Intermedio", Intermedios),
            ("Difícil", Dificiles),
        };

        foreach (var (dificultad, cantidad) in grupos)
        {
            if (restantes <= 0 || cantidad <= 0) continue;
            var ids = _main.Db.ObtenerEjerciciosPorDificultad(dificultad, Math.Min(cantidad, 6));
            foreach (var id in ids)
            {
                if (restantes-- <= 0) break;
                var imagen = ImageHelper.Decodificar(_main.Db.ObtenerImagen(id), 480);
                if (imagen is not null)
                {
                    VistaPrevia.Add(new VistaPreviaEjercicioViewModel(
                        imagen, $"{Etiqueta} {VistaPrevia.Count + 1}", ObtenerAltoVistaPrevia()));
                }
            }
        }

        OnPropertyChanged(nameof(HayVistaPrevia));
        OnPropertyChanged(nameof(TextoVistaPrevia));
    }

    private double ObtenerAltoVistaPrevia()
    {
        return ImagenesMismoTamano ? Math.Clamp(ObtenerTamanoImagen() * 37.8, 45.0, 220.0) : 125.0;
    }

    public void GuardarConfiguracion(ConfiguracionPdf config, ConfiguracionDocumento documento)
    {
        Basicos = config.Basicos;
        Intermedios = config.Intermedios;
        Dificiles = config.Dificiles;
        Titulo = documento.Titulo;
        Autor = documento.Autor;
        Etiqueta = documento.Etiqueta;
        AgregarEspacio = documento.EspacioCm > 0;
        if (documento.EspacioCm > 0)
        {
        EspacioTexto = documento.EspacioCm.ToString("0.0", CultureInfo.InvariantCulture);
        }
        ImagenesMismoTamano = documento.ImagenesMismoTamano;
        TamanoImagenTexto = documento.TamanoImagenCm.ToString("0.0", CultureInfo.InvariantCulture);
    }
}

public sealed class VistaPreviaEjercicioViewModel : IDisposable
{
    public Bitmap Imagen { get; }
    public string Etiqueta { get; }
    public double AltoImagen { get; }

    public VistaPreviaEjercicioViewModel(Bitmap imagen, string etiqueta, double altoImagen)
    {
        Imagen = imagen;
        Etiqueta = etiqueta;
        AltoImagen = altoImagen;
    }

    public void Dispose() => Imagen.Dispose();
}
