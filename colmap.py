import pycolmap
from pathlib import Path
import open3d as o3d
import numpy as np
import matplotlib as plt
import trimesh
import sys
import shutil

n_watkow = 8 # Ile wątków
uzywacGPU = False # Czy robic z GPU

# Ścieżki
zdjecia_dir = Path("./zdjecia")
output_dir = Path("./output")
reco_dir = Path("./output/reconstructions")
undistort_dir = Path("./undistort")
chmury_dir = Path("./chmury")

# Tworzenie output jeżeli go nima
output_dir.mkdir(exist_ok=True)
reco_dir.mkdir(exist_ok=True)
undistort_dir.mkdir(exist_ok=True)
chmury_dir.mkdir(exist_ok=True)

def czy_istnieje_rekonstrukcja():
    ply_path = output_dir / "chmurka.PLY"
    
    if reco_dir.exists() and ply_path.exists():
        if any(reco_dir.iterdir()):
            print("Znaleziono istniejącą rekonstrukcję")
            return True
    return False
def colmap():
  # Ekstrakcja ficzerów
  pycolmap.extract_features(
    database_path = output_dir / "bazunia.db",
    image_path = zdjecia_dir,
    camera_mode=pycolmap.CameraMode.AUTO,
    sift_options=pycolmap.SiftExtractionOptions(
      num_threads=n_watkow,
      use_gpu=uzywacGPU,
      max_num_features = 3000
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
      database_path=output_dir/ "bazunia.db",
      image_path=zdjecia_dir,
      output_path=output_dir,
      options=pycolmap.IncrementalPipelineOptions(
        num_threads=n_watkow,
        ba_use_gpu=uzywacGPU
      )
    )
    return rekonstrukcja

  # Odpalajjj to
  #zwraca slownik, gdzie klucz to int takie id, jesli bedzie
  #pare rekonstrukcji to beda numerowane 0, 1, 2, ...
  rek_dict = wlacz_rekonstrukcje(zdjecia_dir, output_dir)

  #dla ulatwienia na poczatku wezmy tylko pierwsze
  if rek_dict[0] is not None:
      rek = rek_dict[0]
      print(f"Zrekonstruowano coś!")
      print(f"Zarejestrowano {len(rek.images)} zdjęć")
      print(f"Utworzono {len(rek.points3D)} punktów 3D")
      rek.export_PLY(output_dir / "chmurka.PLY")
      rek.write(output_dir / "reconstructions")

  rek_dict[0].write(output_dir / "reconstructions")

if not czy_istnieje_rekonstrukcja():
   colmap()
zaladowana_rekonstrukcja = pycolmap.Reconstruction(output_dir / "reconstructions")

#odzniekształcanie (undistort lol) zdjęć i zapisywanie ich i innych rzeczy
#(cale drzewo katalogowe) odpowiednio dla PMVS :D
pycolmap.undistort_images(
    output_path="./undistort",
    input_path="./output/0",
    image_path="./zdjecia",
    output_type='PMVS',
)

#i do pmvs2
import subprocess
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
pmvs2_executable = os.path.join(base_dir, "dependencies", "pmvs2")
prefix = os.path.join(base_dir, "undistort", "pmvs/") #colmap wyżej powinien go stworzyc
option_file = "option-all"#<- wewnatrz /undistort/pmvs 
#dam go tu bo idk gdzie, zeby zobaczyc jakie sa opjce w pmvs2
#wystarczy uruchomic go i wyswietli ładnie :)

#taka komenda np wlaczylem:
#./dependencies/CMVS-PMVS/program/OutputLinux/main/pmvs2 ./undistort/pmvs/ ./pmvs_options.txt
#program, „prefix” czyli katalog ten pmvs i potem opcje ktore maja swoj format taki prosty
#ale musza byc wewnatrz folderu pmvs
subprocess.run(
  [pmvs2_executable, prefix, option_file], 
  check=True
  )
#w ./undistort/pmvs/models wypluje model o nazwie <nazwa pliku z opcjami>.ply xD

if(len(sys.argv) > 1):
  stara_nazwa = option_file + ".ply"
  nowa_nazwa = sys.argv[1] + ".ply"
  stary_plik = os.path.join(base_dir, "undistort/pmvs/models/", stara_nazwa)
  nowy_plik = os.path.join(base_dir, "chmury/", nowa_nazwa)
  shutil.move(str(stary_plik), str(nowy_plik))