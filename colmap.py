import pycolmap
from pathlib import Path

n_watkow = 2 # Ile wątków
uzywacGPU = False # Czy robic z GPU

# Ścieżki
zdjecia_dir = Path("./zdjecia")
output_dir = Path("./output")

# Tworzenie output jeżeli go nima
output_dir.mkdir(exist_ok=True)

# Ekstrakcja ficzerów
pycolmap.extract_features(
  database_path = output_dir / "bazunia.db",
  image_path = zdjecia_dir,
  camera_mode=pycolmap.CameraMode.AUTO,
  sift_options=pycolmap.SiftExtractionOptions(
    num_threads=n_watkow,
    use_gpu=uzywacGPU
  )
)

# Matching ficzerów
pycolmap.match_sequential(
  database_path = output_dir / "bazunia.db",
  sift_options=pycolmap.SiftMatchingOptions(
    num_threads=n_watkow,
    use_gpu=uzywacGPU
  )
)

# Rekonstrukcja
def wlacz_rekonstrukcje(zdjecia_dir, output_dir):
  rekonstrukcja = pycolmap.incremental_mapping(
    database_path=output_path/ "bazunia.db",
    image_path=zdjecia_dir,
    output_path=output_dir,
    options=pycolmap.IncrementalPipelineOptions(
      num_threads=n_watkow,
      use_gpu=uzywacGPU
    )
  )
  return rekonstrukcja

# Odpalajjj to
rekonstrukcja = wlacz_rekonstrukcje(zdjecia_dir, output_dir)

if rekonstrukcja is not None:
  print(f"Zrekonstruowano coś!")
  print(f"Zarejestrowano {len(rekonstrukcja.images)} zdjęć")
  print(f"Utworzono {len(rekonstrukcja.points3D)} puntków 3D")
  rekonstrukcja.export_PLY(output_dir / "chmurka.PLY")

rekonstrukcja.write(output_dir / "rekonstrukcja")
zaladowana_rekonstrukcja = pycolmap.Reconstruction(output_dir / "rekonstrukcja")