using System;
using System.Globalization;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using GeneradorEjerciciosAvalonia.Models;

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

    public string[] Etiquetas => Constantes.EtiquetasDocumento;

    public string TotalTexto => $"📊 Total de ejercicios: {Basicos + Intermedios + Dificiles}";

    public GenerarViewModel(MainViewModel main)
    {
        _main = main;
    }

    partial void OnBasicosChanged(int value) => OnPropertyChanged(nameof(TotalTexto));
    partial void OnIntermediosChanged(int value) => OnPropertyChanged(nameof(TotalTexto));
    partial void OnDificilesChanged(int value) => OnPropertyChanged(nameof(TotalTexto));

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
        };
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
    }
}
