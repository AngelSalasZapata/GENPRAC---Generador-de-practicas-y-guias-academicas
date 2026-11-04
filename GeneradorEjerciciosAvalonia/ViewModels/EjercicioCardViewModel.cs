using Avalonia.Media;
using Avalonia.Media.Imaging;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using GeneradorEjerciciosAvalonia.Models;

namespace GeneradorEjerciciosAvalonia.ViewModels;

public partial class EjercicioCardViewModel : ViewModelBase
{
    private readonly BancoViewModel _parent;

    public int Id { get; }
    public string Nombre { get; }
    public string Dificultad { get; }

    public IBrush ColorDificultad { get; }
    public IBrush FondoDificultad { get; }

    [ObservableProperty] private Bitmap? _imagen;
    [ObservableProperty] private bool _cargando = true;

    public EjercicioResumen Resumen => new()
    {
        Id = Id,
        Nombre = Nombre,
        Dificultad = Dificultad,
    };

    public EjercicioCardViewModel(EjercicioResumen resumen, BancoViewModel parent)
    {
        _parent = parent;
        Id = resumen.Id;
        Nombre = resumen.Nombre;
        Dificultad = resumen.Dificultad;
        ColorDificultad = Brush.Parse(Constantes.ColorDe(resumen.Dificultad));
        FondoDificultad = Brush.Parse(Constantes.FondoDe(resumen.Dificultad));
    }

    [RelayCommand]
    private void Ver() => _parent.VerEjercicio(Resumen);

    [RelayCommand]
    private void Eliminar() => _parent.EliminarEjercicio(this);
}
