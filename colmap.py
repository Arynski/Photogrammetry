import pycolmap
from pathlib import Path
import open3d as o3d
import numpy as np
import sys
import shutil
import hashlib

# Ścieżki
katalog = Path(__file__).resolve().parent
zdjecia_dir = katalog / Path("work/zdjecia")
output_dir = katalog / Path("work/output")
reco_dir = katalog / Path("work/output/reconstructions")
undistort_dir = katalog / Path("work/undistort")
dependencies_dir = katalog / Path("dependencies")
chmury_dir = katalog / Path("chmury")
zdjecia_hash = katalog / Path("work/img_hash")
#tworzenie katalogow
output_dir.mkdir(exist_ok=True)
reco_dir.mkdir(exist_ok=True)
undistort_dir.mkdir(exist_ok=True)
chmury_dir.mkdir(exist_ok=True)
zdjecia_hash.touch(exist_ok=True)

podana_nazwa = None
n_watkow = 8 # Ile wątków
uzywacGPU = False # Czy robic z GPU

#oblicza hasz katalogu z czasow, program sam sprawdzi czy katalog ze zdjeciami sie zmienil i 
#na podstawie tego zrobi co trzeba
def haszuj_katalog(path: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(path.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(path)).encode())
            h.update(str(p.stat().st_mtime_ns).encode())
    return h.hexdigest()

#hasz dalej potrzebny nawet jesli -f, bo na koncu trzeba nadpisac
hash_nowy = haszuj_katalog(zdjecia_dir) 
if(not "-f" in sys.argv):
  with open(str(zdjecia_hash)) as f:
      hash_stary = f.readline().strip()

  czy_zmieniono_zdjecia = (hash_nowy != hash_stary)

  #program juz sie wykonal wczesniej, caly, na tych zdjeciach
  if(not czy_zmieniono_zdjecia):
    print("Program już został wykonany na tych zdjeciach! Aby wymusic użyj opcji -f.")
    sys.exit(0)
  else: #jesli mamy nowe zdjecia to wyczyscmy katalogi
    if output_dir.exists():
      shutil.rmtree(output_dir)
      output_dir.mkdir(exist_ok=True)
      reco_dir.mkdir(exist_ok=True)

if "-o" in sys.argv:
    gdzie_nazwa = sys.argv.index("-o") + 1
    podana_nazwa = sys.argv[gdzie_nazwa] if gdzie_nazwa < len(sys.argv) else None
    print("Podana nazwa:", podana_nazwa, "Szukaj w chmurka :)")
else:
    print("Nie podano nazwy wyjsciowego modulu. Szukaj w", str((undistort_dir / "pmvs/models")))

if "-nthreads" in sys.argv:
  ile_watkow_idx = sys.argv.index("-nthreads") + 1
  n_watkow = int(sys.argv[ile_watkow_idx])

#nie wydaje sie potrzebne razem z rozwiazaniem z haszami, bo jedyna sytuacja jaka
#zachodzi to albo te same, albo stare zdjecia -- po co wywoływać jeszcze raz cały program, albo
#nawet tylko jego czesc jesli nie zmienily sie zdjecia? Zresztą można z opcją -f.
#def czy_istnieje_rekonstrukcja():
#    ply_path = output_dir / "chmurka.PLY"
#    
#    if reco_dir.exists() and ply_path.exists():
#        if any(reco_dir.iterdir()):
#            print("Znaleziono istniejącą rekonstrukcję")
#            return True
#    return False

def colmap():
  # Ekstrakcja ficzerów
  pycolmap.extract_features(
    database_path = output_dir / "bazunia.db",
    image_path = zdjecia_dir,
    camera_mode=pycolmap.CameraMode.AUTO,
    sift_options=pycolmap.SiftExtractionOptions(
      num_threads=n_watkow,
      use_gpu=uzywacGPU,
      max_num_features = 1500
    )
  )

  # Matching ficzerów
  #pycolmap.match_sequential(
  #  database_path = output_dir / "bazunia.db",
  #  sift_options=pycolmap.SiftMatchingOptions(
  #    num_threads=n_watkow,
  #    use_gpu=uzywacGPU
  #  )
  #)

  #uzywajac drzewa
  pycolmap.match_vocabtree(
    database_path = output_dir / "bazunia.db",
    matching_options = pycolmap.VocabTreeMatchingOptions(
        num_nearest_neighbors = 5,           #ile najbliższych zdjec porownywac, ok 5-10
        num_checks = 200,            #im wiecej tym lepiej ale wolniej : /
        num_threads = n_watkow,
        vocab_tree_path = dependencies_dir / "vocab_tree_flickr100K_words32K.bin"
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
        ba_refine_focal_length=False,
        ba_refine_principal_point=False,
        ba_refine_extra_params=False,
        ba_global_max_num_iterations=50,
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

#depracted vvv
#if not czy_istnieje_rekonstrukcja():
colmap()
#depracted vvv
#zaladowana_rekonstrukcja = pycolmap.Reconstruction(output_dir / "reconstructions")

#odzniekształcanie (undistort lol) zdjęć i zapisywanie ich i innych rzeczy
#(cale drzewo katalogowe) odpowiednio dla PMVS :D
pycolmap.undistort_images(
    output_path=undistort_dir,
    input_path=output_dir/"0",
    image_path=zdjecia_dir,
    output_type='PMVS',
)

#i do pmvs2
import subprocess
import os

pmvs2_exec = dependencies_dir / "pmvs2"
prefix = undistort_dir / "pmvs/" #colmap wyżej powinien go stworzyc
option_file = "option-all" # <- wewnatrz /undistort/pmvs 
#dam go tu bo idk gdzie, zeby zobaczyc jakie sa opjce w pmvs2
#wystarczy uruchomic go i wyswietli ładnie :)
print(pmvs2_exec, prefix, option_file)

#taka komenda np wlaczylem:
#./dependencies/CMVS-PMVS/program/OutputLinux/main/pmvs2 ./undistort/pmvs/ ./pmvs_options.txt
#program, „prefix” czyli katalog ten pmvs i potem opcje ktore maja swoj format taki prosty
#ale musza byc wewnatrz folderu pmvs
subprocess.run(
  [str(pmvs2_exec), str(prefix)+"/", option_file], 
  check=True
  )
#w ./undistort/pmvs/models wypluje model o nazwie <nazwa pliku z opcjami>.ply xD

if(podana_nazwa != None):
  stara_nazwa = option_file + ".ply"
  nowa_nazwa = podana_nazwa + ".ply"
  stary_plik = undistort_dir / "pmvs/models/" / stara_nazwa
  nowy_plik = chmury_dir / nowa_nazwa
  shutil.move(str(stary_plik), str(nowy_plik))

#program sie cały wykonał, zmieniamy hash
with open(str(zdjecia_hash), "w") as f:
  f.write(hash_nowy)