using System;
using System.Collections.Generic;

namespace GeneradorEjerciciosAvalonia.Models;

public sealed class EjercicioResumen
{
    public int Id { get; set; }
    public string Nombre { get; set; } = string.Empty;
    public string Dificultad { get; set; } = string.Empty;
}

public sealed class Ejercicio
{
    public int Id { get; set; }
    public string Nombre { get; set; } = string.Empty;
    public string Dificultad { get; set; } = string.Empty;
    public byte[] Imagen { get; set; } = Array.Empty<byte>();
}

public sealed class ConfiguracionPdf
{
    public int Basicos { get; set; } = 30;
    public int Intermedios { get; set; } = 20;
    public int Dificiles { get; set; } = 10;
    public int Total => Basicos + Intermedios + Dificiles;
}

public sealed class ConfiguracionDocumento
{
    public const string TituloPorDefecto = "Guía de Prácticas Académicas";
    public const string AutorPorDefecto = "Angel Fabiano Salas Zapata";
    public const string EtiquetaPorDefecto = "Ejercicio";

    public string Titulo { get; set; } = TituloPorDefecto;
    public string Autor { get; set; } = AutorPorDefecto;
    public string Etiqueta { get; set; } = EtiquetaPorDefecto;
    public double EspacioCm { get; set; } = 0.0;
}

public sealed class EstadisticasBanco
{
    public int Total { get; set; }
    public int Basicos { get; set; }
    public int Intermedios { get; set; }
    public int Dificiles { get; set; }

    public static EstadisticasBanco DesdeConteo(IReadOnlyDictionary<string, int> conteo)
    {
        return new EstadisticasBanco
        {
            Basicos = conteo.TryGetValue("Básico", out var b) ? b : 0,
            Intermedios = conteo.TryGetValue("Intermedio", out var i) ? i : 0,
            Dificiles = conteo.TryGetValue("Difícil", out var d) ? d : 0,
        };
    }

    public bool EstaCompleto => Basicos >= Constantes.ObjetivoBasico
                                && Intermedios >= Constantes.ObjetivoIntermedio
                                && Dificiles >= Constantes.ObjetivoDificil;
}

public static class Constantes
{
    public const int ObjetivoBasico = 30;
    public const int ObjetivoIntermedio = 20;
    public const int ObjetivoDificil = 10;

    public static readonly string[] Dificultades = { "Básico", "Intermedio", "Difícil" };
    public static readonly string[] EtiquetasDocumento = { "Ejercicio", "Enunciado", "Problema", "Pregunta", "Actividad" };

    private static readonly Dictionary<string, string> ColoresMap = new()
    {
        ["Básico"] = "#27ae60",
        ["Intermedio"] = "#f39c12",
        ["Difícil"] = "#e74c3c",
    };

    private static readonly Dictionary<string, string> FondosMap = new()
    {
        ["Básico"] = "#eafaf1",
        ["Intermedio"] = "#fef5e7",
        ["Difícil"] = "#fdedec",
    };

    public static string ColorDe(string dificultad) =>
        ColoresMap.TryGetValue(dificultad, out var c) ? c : "#95a5a6";

    public static string FondoDe(string dificultad) =>
        FondosMap.TryGetValue(dificultad, out var f) ? f : "#ecf0f1";
}
