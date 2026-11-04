using Avalonia.Media.Imaging;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using GeneradorEjerciciosAvalonia.Models;

namespace GeneradorEjerciciosAvalonia.ViewModels;

public partial class FilaCargaViewModel : ViewModelBase
{
    private readonly CargaMasivaViewModel _parent;

    public byte[] Datos { get; }
    public Bitmap Preview { get; }
    public string[] Dificultades => Constantes.Dificultades;

    [ObservableProperty] private int _numero;
    [ObservableProperty] private string _nombre;
    [ObservableProperty] private string _dificultad = "Básico";

    public FilaCargaViewModel(CargaMasivaViewModel parent, byte[] datos, Bitmap preview, string nombre)
    {
        _parent = parent;
        Datos = datos;
        Preview = preview;
        _nombre = nombre;
    }

    [RelayCommand]
    private void Quitar() => _parent.Quitar(this);
}
