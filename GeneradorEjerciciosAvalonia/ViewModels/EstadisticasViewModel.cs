using System;
using System.Linq;
using Avalonia.Media;
using CommunityToolkit.Mvvm.ComponentModel;
using GeneradorEjerciciosAvalonia.Models;

namespace GeneradorEjerciciosAvalonia.ViewModels;

public partial class EstadisticasViewModel : ViewModelBase
{
    private const double AnchoBaseBarra = 320.0;

    private readonly MainViewModel _main;
    private bool _inicializado;

    [ObservableProperty] private bool _esVisible;
    [ObservableProperty] private int _basicos;
    [ObservableProperty] private int _intermedios;
    [ObservableProperty] private int _dificiles;
    [ObservableProperty] private int _total;

    [ObservableProperty] private double _anchoBasico = 10;
    [ObservableProperty] private double _anchoIntermedio = 10;
    [ObservableProperty] private double _anchoDificil = 10;

    [ObservableProperty] private string _estadoBasico = string.Empty;
    [ObservableProperty] private string _estadoIntermedio = string.Empty;
    [ObservableProperty] private string _estadoDificil = string.Empty;

    [ObservableProperty] private bool _estaCompleto;

    public IBrush ColorBasico { get; } = Brush.Parse(Constantes.ColorDe("Básico"));
    public IBrush ColorIntermedio { get; } = Brush.Parse(Constantes.ColorDe("Intermedio"));
    public IBrush ColorDificil { get; } = Brush.Parse(Constantes.ColorDe("Difícil"));

    public string ObjetivoTexto =>
        $"Distribución objetivo: {Constantes.ObjetivoBasico} Básicos • " +
        $"{Constantes.ObjetivoIntermedio} Intermedios • {Constantes.ObjetivoDificil} Difíciles";

    public EstadisticasViewModel(MainViewModel main)
    {
        _main = main;
    }

    public void OnMostrar() => Refrescar();

    public void Refrescar()
    {
        var conteo = _main.Db.ContarPorDificultad();
        var b = conteo.TryGetValue("Básico", out var vb) ? vb : 0;
        var i = conteo.TryGetValue("Intermedio", out var vi) ? vi : 0;
        var d = conteo.TryGetValue("Difícil", out var vd) ? vd : 0;

        if (_inicializado && b == Basicos && i == Intermedios && d == Dificiles)
        {
            return;
        }

        _inicializado = true;

        Basicos = b;
        Intermedios = i;
        Dificiles = d;
        Total = b + i + d;

        var max = Math.Max(1, Math.Max(b, Math.Max(i, d)));
        AnchoBasico = Math.Max(10, AnchoBaseBarra * b / max);
        AnchoIntermedio = Math.Max(10, AnchoBaseBarra * i / max);
        AnchoDificil = Math.Max(10, AnchoBaseBarra * d / max);

        EstadoBasico = Estado(b, Constantes.ObjetivoBasico);
        EstadoIntermedio = Estado(i, Constantes.ObjetivoIntermedio);
        EstadoDificil = Estado(d, Constantes.ObjetivoDificil);

        EstaCompleto = b >= Constantes.ObjetivoBasico
                       && i >= Constantes.ObjetivoIntermedio
                       && d >= Constantes.ObjetivoDificil;

        OnPropertyChanged(nameof(ObjetivoTexto));
    }

    private static string Estado(int valor, int minimo) =>
        valor >= minimo ? "✅ Objetivo cumplido" : "⚠️ Faltan ejercicios";
}
