using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Media;
using Avalonia.Platform.Storage;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using GeneradorEjerciciosAvalonia.Models;
using GeneradorEjerciciosAvalonia.Services;
using GeneradorEjerciciosAvalonia.Views;

namespace GeneradorEjerciciosAvalonia.ViewModels;

public partial class MainViewModel : ViewModelBase
{
    private static readonly IBrush Accent = Brush.Parse("#00b4d8");

    public DatabaseService Db { get; }

    public Window? Owner { get; set; }

    public GenerarViewModel Generar { get; }
    public BancoViewModel Banco { get; }
    public EstadisticasViewModel Estadisticas { get; }

    public bool BancoDirty { get; set; } = true;

    [ObservableProperty]
    private string _seccionActiva = "generar";

    public MainViewModel()
    {
        Db = new DatabaseService();
        Generar = new GenerarViewModel(this);
        Banco = new BancoViewModel(this);
        Estadisticas = new EstadisticasViewModel(this);
        Generar.EsVisible = true;
    }

    public bool EsGenerar => SeccionActiva == "generar";
    public bool EsBanco => SeccionActiva == "banco";
    public bool EsStats => SeccionActiva == "stats";

    public IBrush FondoGenerar => EsGenerar ? Accent : Brushes.Transparent;
    public IBrush FondoBanco => EsBanco ? Accent : Brushes.Transparent;
    public IBrush FondoStats => EsStats ? Accent : Brushes.Transparent;

    partial void OnSeccionActivaChanged(string value)
    {
        OnPropertyChanged(nameof(EsGenerar));
        OnPropertyChanged(nameof(EsBanco));
        OnPropertyChanged(nameof(EsStats));
        OnPropertyChanged(nameof(FondoGenerar));
        OnPropertyChanged(nameof(FondoBanco));
        OnPropertyChanged(nameof(FondoStats));
    }

    [RelayCommand]
    private void Navegar(string? key)
    {
        key ??= "generar";
        Generar.EsVisible = key == "generar";
        Banco.EsVisible = key == "banco";
        Estadisticas.EsVisible = key == "stats";
        SeccionActiva = key;

        switch (key)
        {
            case "banco":
                Banco.OnMostrar();
                break;
            case "stats":
                Estadisticas.OnMostrar();
                break;
        }
    }

    private void MarcarBancoDirty()
    {
        BancoDirty = true;
        if (Banco.EsVisible)
        {
            Banco.Refrescar();
        }
    }

    public async Task AbrirAgregarAsync()
    {
        if (Owner is null) return;
        var resultado = await AgregarEjercicioWindow.ShowAsync(Owner);
        if (resultado is null) return;

        Db.AgregarEjercicio(resultado.Value.Nombre, resultado.Value.Dificultad, resultado.Value.Imagen);
        MarcarBancoDirty();
        await MessageDialog.InfoAsync(Owner, "Ejercicio agregado",
            $"'{resultado.Value.Nombre}' se agregó correctamente al banco");
    }

    public async Task AbrirCargaMasivaAsync()
    {
        if (Owner is null) return;
        var resultado = await CargaMasivaWindow.ShowAsync(Owner);
        if (resultado is null || resultado.Count == 0) return;

        Db.AgregarEjercicios(resultado);
        MarcarBancoDirty();
        await MessageDialog.InfoAsync(Owner, "Carga masiva",
            $"Se agregaron {resultado.Count} ejercicios al banco");
    }

    public async Task VerEjercicioAsync(EjercicioResumen resumen)
    {
        if (Owner is null) return;
        var bytes = Db.ObtenerImagen(resumen.Id);
        if (bytes is null || bytes.Length == 0) return;

        var ejercicio = new Ejercicio
        {
            Id = resumen.Id,
            Nombre = resumen.Nombre,
            Dificultad = resumen.Dificultad,
            Imagen = bytes,
        };
        await VistaPreviaWindow.ShowAsync(Owner, ejercicio);
    }

    public async Task EliminarEjercicioAsync(int id)
    {
        if (Owner is null) return;
        var confirmado = await MessageDialog.ConfirmAsync(Owner, "Confirmar eliminación",
            "¿Está seguro de eliminar este ejercicio?");
        if (!confirmado) return;

        Db.EliminarEjercicio(id);
        MarcarBancoDirty();
    }

    public async Task GenerarPdfAsync(GenerarViewModel generar)
    {
        if (Owner is null) return;

        var config = generar.ObtenerConfig();
        if (config.Total == 0)
        {
            await MessageDialog.InfoAsync(Owner, "Sin ejercicios", "Seleccione al menos 1 ejercicio");
            return;
        }

        var archivo = await Owner.StorageProvider.SaveFilePickerAsync(new FilePickerSaveOptions
        {
            Title = "Guardar PDF",
            SuggestedFileName = "ejercicios_generados.pdf",
            DefaultExtension = "pdf",
            FileTypeChoices = new[]
            {
                new FilePickerFileType("Documento PDF") { Patterns = new[] { "*.pdf" } },
            },
        });
        if (archivo is null) return;

        var ruta = archivo.Path.LocalPath;
        var documento = generar.ObtenerDocumento();

        var conteo = Db.ContarPorDificultad();
        var faltantes = new List<string>();
        void Verificar(string dificultad, int cantidad)
        {
            if (cantidad <= 0) return;
            var disponibles = conteo.TryGetValue(dificultad, out var v) ? v : 0;
            if (disponibles < cantidad)
            {
                faltantes.Add($"  • {dificultad}: disponibles {disponibles} / pedidos {cantidad}");
            }
        }
        Verificar("Básico", config.Basicos);
        Verificar("Intermedio", config.Intermedios);
        Verificar("Difícil", config.Dificiles);

        if (faltantes.Count > 0)
        {
            var mensaje = "No hay suficientes ejercicios en el banco:\n\n"
                          + string.Join("\n", faltantes)
                          + "\n\n¿Generar con los disponibles?";
            if (!await MessageDialog.ConfirmAsync(Owner, "Ejercicios insuficientes", mensaje))
            {
                return;
            }
        }

        generar.GuardarConfiguracion(config, documento);

        var progreso = new ProgressWindow("Generando PDF...");
        _ = progreso.ShowDialog(Owner);

        await Task.Run(() =>
        {
            try
            {
                var ids = new List<int>();
                var etapas = new (string Dificultad, int Cantidad, double Progreso)[]
                {
                    ("Básico", config.Basicos, 0.2),
                    ("Intermedio", config.Intermedios, 0.45),
                    ("Difícil", config.Dificiles, 0.7),
                };

                foreach (var (dificultad, cantidad, avance) in etapas)
                {
                    if (cantidad <= 0) continue;
                    var dif = dificultad;
                    Dispatcher.UIThread.Post(() => progreso.Actualizar($"Seleccionando ejercicios {dif}...", avance));
                    ids.AddRange(Db.ObtenerEjerciciosPorDificultad(dificultad, cantidad));
                }

                if (ids.Count == 0)
                {
                    Dispatcher.UIThread.Post(() =>
                    {
                        progreso.Close();
                        _ = MessageDialog.InfoAsync(Owner, "Error", "No hay ejercicios disponibles");
                    });
                    return;
                }

                Barajar(ids);
                Dispatcher.UIThread.Post(() => progreso.Actualizar("Construyendo documento PDF...", 0.85));
                PdfGenerator.GenerarPdfEjercicios(ids, ruta, documento, Db.ObtenerImagen);

                Dispatcher.UIThread.Post(() =>
                {
                    progreso.Close();
                    _ = MessageDialog.InfoAsync(Owner, "PDF generado", $"El archivo se guardó en:\n{ruta}");
                });
            }
            catch (Exception ex)
            {
                Dispatcher.UIThread.Post(() =>
                {
                    progreso.Close();
                    _ = MessageDialog.InfoAsync(Owner, "Error", ex.Message);
                });
            }
        });
    }

    private static void Barajar(IList<int> lista)
    {
        var rng = Random.Shared;
        for (var i = lista.Count - 1; i > 0; i--)
        {
            var j = rng.Next(i + 1);
            (lista[i], lista[j]) = (lista[j], lista[i]);
        }
    }
}
