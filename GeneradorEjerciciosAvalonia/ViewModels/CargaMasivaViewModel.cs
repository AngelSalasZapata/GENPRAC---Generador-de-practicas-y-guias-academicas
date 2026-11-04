using System.Collections.Generic;
using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using GeneradorEjerciciosAvalonia.Models;

namespace GeneradorEjerciciosAvalonia.ViewModels;

public partial class CargaMasivaViewModel : ViewModelBase
{
    public ObservableCollection<FilaCargaViewModel> Filas { get; } = new();

    public string[] Dificultades => Constantes.Dificultades;

    [ObservableProperty] private string _dificultadAplicar = "Básico";
    [ObservableProperty] private string _conteoTexto = "0 imágenes cargadas";
    [ObservableProperty] private bool _vacio = true;

    public void Limpiar()
    {
        Filas.Clear();
        Actualizar();
    }

    public void AgregarFila(FilaCargaViewModel fila)
    {
        fila.Numero = Filas.Count + 1;
        Filas.Add(fila);
        Actualizar();
    }

    public void Quitar(FilaCargaViewModel fila)
    {
        Filas.Remove(fila);
        Renumerar();
        Actualizar();
    }

    public IReadOnlyList<(string Nombre, string Dificultad, byte[] Imagen)> ConstruirResultado()
    {
        var resultado = new List<(string, string, byte[])>();
        for (var i = 0; i < Filas.Count; i++)
        {
            var fila = Filas[i];
            var nombre = string.IsNullOrWhiteSpace(fila.Nombre) ? $"Ejercicio {i + 1}" : fila.Nombre.Trim();
            resultado.Add((nombre, fila.Dificultad, fila.Datos));
        }
        return resultado;
    }

    [RelayCommand]
    private void AplicarATodas()
    {
        foreach (var fila in Filas)
        {
            fila.Dificultad = DificultadAplicar;
        }
    }

    private void Renumerar()
    {
        for (var i = 0; i < Filas.Count; i++)
        {
            Filas[i].Numero = i + 1;
        }
    }

    private void Actualizar()
    {
        Vacio = Filas.Count == 0;
        ConteoTexto = $"{Filas.Count} imagen(es) cargada(s)";
    }
}
