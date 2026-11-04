using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Media.Imaging;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using GeneradorEjerciciosAvalonia.Models;
using GeneradorEjerciciosAvalonia.Services;

namespace GeneradorEjerciciosAvalonia.ViewModels;

public partial class BancoViewModel : ViewModelBase
{
    private readonly MainViewModel _main;

    private readonly Dictionary<int, EjercicioCardViewModel> _cards = new();
    private readonly Dictionary<int, Bitmap?> _thumbs = new();
    private readonly HashSet<int> _cargando = new();
    private readonly SemaphoreSlim _semaforo = new(4, 4);
    private List<EjercicioResumen> _todos = new();
    private List<EjercicioResumen> _filtrados = new();

    // ── Paginación ──
    private const int TamanoPagina = 24;

    [ObservableProperty] private bool _esVisible;
    [ObservableProperty] private string _busqueda = string.Empty;
    [ObservableProperty] private string _dificultadSeleccionada = "Todas";
    [ObservableProperty] private bool _vacio = true;
    [ObservableProperty] private string _conteoTexto = "0 ejercicio(s)";
    [ObservableProperty] private int _paginaActual = 1;
    [ObservableProperty] private int _totalPaginas = 1;
    [ObservableProperty] private bool _puedeIrAtras;
    [ObservableProperty] private bool _puedeIrAdelante;

    public ObservableCollection<EjercicioCardViewModel> Ejercicios { get; } = new();

    public string[] Dificultades { get; } = { "Todas", "Básico", "Intermedio", "Difícil" };

    public BancoViewModel(MainViewModel main)
    {
        _main = main;
    }

    public void OnMostrar()
    {
        if (_main.BancoDirty)
        {
            Refrescar();
        }
    }

    public void Refrescar()
    {
        _todos = _main.Db.ObtenerEjerciciosLista();
        _main.BancoDirty = false;

        var idsValidos = _todos.Select(e => e.Id).ToHashSet();
        foreach (var id in _cards.Keys.Where(id => !idsValidos.Contains(id)).ToList())
            _cards.Remove(id);
        foreach (var id in _thumbs.Keys.Where(id => !idsValidos.Contains(id)).ToList())
            _thumbs.Remove(id);

        AplicarFiltro();
    }

    partial void OnBusquedaChanged(string value) => AplicarFiltro();
    partial void OnDificultadSeleccionadaChanged(string value) => AplicarFiltro();

    private void AplicarFiltro()
    {
        var consulta = (Busqueda ?? string.Empty).Trim();
        var dificultad = DificultadSeleccionada;

        _filtrados = _todos.Where(e =>
                (dificultad == "Todas" || e.Dificultad == dificultad) &&
                (consulta.Length == 0 || e.Nombre.Contains(consulta, StringComparison.OrdinalIgnoreCase)))
            .ToList();

        // Resetear a página 1 al cambiar filtros
        PaginaActual = 1;
        ActualizarPagina();
    }

    private void ActualizarPagina()
    {
        TotalPaginas = Math.Max(1, (int)Math.Ceiling(_filtrados.Count / (double)TamanoPagina));
        PaginaActual = Math.Clamp(PaginaActual, 1, TotalPaginas);
        PuedeIrAtras = PaginaActual > 1;
        PuedeIrAdelante = PaginaActual < TotalPaginas;

        var pagina = _filtrados
            .Skip((PaginaActual - 1) * TamanoPagina)
            .Take(TamanoPagina)
            .ToList();

        Ejercicios.Clear();
        foreach (var resumen in pagina)
            Ejercicios.Add(ObtenerCard(resumen));

        Vacio = _filtrados.Count == 0;
        ConteoTexto = _filtrados.Count == 0
            ? "Sin resultados"
            : $"{_filtrados.Count} ejercicio(s) — Página {PaginaActual} / {TotalPaginas}";
    }

    [RelayCommand]
    private void PaginaAnterior()
    {
        if (PaginaActual <= 1) return;
        PaginaActual--;
        ActualizarPagina();
    }

    [RelayCommand]
    private void PaginaSiguiente()
    {
        if (PaginaActual >= TotalPaginas) return;
        PaginaActual++;
        ActualizarPagina();
    }

    private EjercicioCardViewModel ObtenerCard(EjercicioResumen resumen)
    {
        if (_cards.TryGetValue(resumen.Id, out var card))
        {
            return card;
        }

        card = new EjercicioCardViewModel(resumen, this);
        _cards[resumen.Id] = card;
        AsegurarMiniatura(card);
        return card;
    }

    private void AsegurarMiniatura(EjercicioCardViewModel card)
    {
        if (_thumbs.TryGetValue(card.Id, out var cacheada))
        {
            card.Imagen = cacheada;
            card.Cargando = false;
            return;
        }

        if (!_cargando.Add(card.Id)) return;

        var id = card.Id;
        _ = Task.Run(async () =>
        {
            await _semaforo.WaitAsync();
            try
            {
                // Usa miniatura ligera en primer lugar; solo cae a imagen completa si no hay miniatura
                var bytes = _main.Db.ObtenerMiniatura(id);
                var bitmap = ImageHelper.Decodificar(bytes, 320);
                Dispatcher.UIThread.Post(() =>
                {
                    _thumbs[id] = bitmap;
                    _cargando.Remove(id);
                    card.Imagen = bitmap;
                    card.Cargando = false;
                });
            }
            finally
            {
                _semaforo.Release();
            }
        });
    }

    public void VerEjercicio(EjercicioResumen resumen) => _ = _main.VerEjercicioAsync(resumen);

    public void EliminarEjercicio(EjercicioCardViewModel card) => _ = _main.EliminarEjercicioAsync(card.Id);

    [RelayCommand]
    private void Agregar() => _ = _main.AbrirAgregarAsync();

    [RelayCommand]
    private void CargarVarios() => _ = _main.AbrirCargaMasivaAsync();
}
