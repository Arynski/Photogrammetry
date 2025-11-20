import pycolmap
from pathlib import Path
import open3d as o3d
import numpy as np
import sys
import shutil
import hashlib
import logging
import yaml

# Ścieżki
katalog = Path(__file__).resolve().parent
zdjecia_dir = katalog / Path("work/zdjecia")
output_dir = katalog / Path("work/output")
reco_dir = katalog / Path("work/output/reconstructions")
undistort_dir = katalog / Path("work/undistort")
dependencies_dir = katalog / Path("dependencies")
chmury_dir = katalog / Path("chmury")
zdjecia_hash = katalog / Path("work/img_hash")
logi = katalog / Path("work/log")
opcje = katalog / Path("work/options.yaml")
#tworzenie katalogow
output_dir.mkdir(exist_ok=True)
reco_dir.mkdir(exist_ok=True)
undistort_dir.mkdir(exist_ok=True)
chmury_dir.mkdir(exist_ok=True)
zdjecia_hash.touch(exist_ok=True)
logi.touch(exist_ok=True)

podana_nazwa = None
n_watkow = 8 # Ile wątków
uzywacGPU = False # Czy robic z GPU
zlozonosc = 0

#konfiguracja pliku do logowania
logging.basicConfig(
    filename=str(logi),
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

#czy jest w ogole plik z ustawieniami
if not opcje.exists():
    raise FileNotFoundError(f"Nie znaleziono pliku opcji YAML: {opcje}")

#configs["Options"][0] to slownik najszybszych ustawien, 1 srednich a 2 takich mocarnyyyych
with open(str(opcje), "r") as f:
    configs = yaml.safe_load(f)
    
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
if(not "-f" in sys.argv and not '-r' in sys.argv):
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

if "-r" in sys.argv:
  print("Podano opcję -r! Usuwam starą rekonstrukcję.")
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
if "-l" in sys.argv:
    gdzie_zlozonosc = sys.argv.index("-l") + 1
    zlozonosc = int(sys.argv[gdzie_zlozonosc]) if gdzie_zlozonosc < len(sys.argv) else 0
    if(zlozonosc < 0 or zlozonosc > 2):
      zlozonosc = 0
      print(f"Podano nieprawidlowy poziom! Opcje to 0 - najszybsze, 1 - srednie, 2 - dokladne. Domyslnie ustawiono 0")
    else:
      print(f"Podano poziom rekonstrukcji {zlozonosc}")
else:
  print("Nie podano poziomu zlozonosci. Przyjęto 0 (najszybszy).")
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
  logging.info(f"Poczatek colmapowania, plik {podana_nazwa}")
  # Ekstrakcja ficzerów
  pycolmap.extract_features(
    database_path = output_dir / "bazunia.db",
    image_path = zdjecia_dir,
    camera_mode=pycolmap.CameraMode.AUTO,
    sift_options=pycolmap.SiftExtractionOptions(
      num_threads=n_watkow,
      use_gpu=uzywacGPU,
      max_num_features = configs["Options"][zlozonosc]['max_features']
    )
  )
  logging.info("wyekstraktowano")

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
        num_nearest_neighbors = configs["Options"][zlozonosc]['num_nearest_neighbors'],#ile najbliższych zdjec porownywac, ok 5-10
        num_checks = configs["Options"][zlozonosc]['num_checks'],            #im wiecej tym lepiej ale wolniej : /
        num_threads = n_watkow,
        vocab_tree_path = dependencies_dir / "vocab_tree_flickr100K_words32K.bin"
    )
  )
  logging.info("skonczono laczenie")

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
        ba_global_max_num_iterations=configs["Options"][zlozonosc]['ba_global_max_num_iterations'],
        ba_use_gpu=uzywacGPU
      )
    )
    logging.info(f"koniec rekonstrukcji -- stworzylo ich {len(rekonstrukcja)}")
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
logging.info(f"Uruchomienie PMVS2")

#najpierw przerobic plik option-all na takie opcje jakie my chcemy
#po prostu zczytac kazda linie i jesli pierwszy ciag znakow nie jest kluczem w slowniku
#to przepisac, inaczej nowa wartosc. Działa, bo on domyslnie te wartosci co nas interesuja tam ma juz
with open(str(undistort_dir / "pmvs/opcje.txt"), 'w') as nowy:
  with open(str(undistort_dir / "pmvs/option-all"), 'r') as stary:
      for line in stary:
        parts = line.split()
        if not parts:
            nowy.write(line)
            continue
        haslo = parts[0]
        if haslo in configs["Options"][zlozonosc]:
            nowy.write(f"{haslo} {configs['Options'][zlozonosc][haslo]}\n")
        else:
            nowy.write(line)


pmvs2_exec = dependencies_dir / "pmvs2"
prefix = undistort_dir / "pmvs/" #colmap wyżej powinien go stworzyc
option_file = "opcje.txt" # <- wewnatrz /undistort/pmvs 
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

logging.info(f"Koniec")