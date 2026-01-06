import numpy as np
import open3d as o3d
import trimesh
from pathlib import Path
import os
import argparse
import sys
from scipy.spatial import cKDTree

#przyjmuje nazwe pliku ply, zakladamy ze jest w ./chmury
#i ktora metode wykorzystac (0=ball pivoting, 1=poisson, 2=alpha shapes)
parser = argparse.ArgumentParser()
parser.add_argument("filename", help="nazwa pliku PLY (sam plik, bez ścieżki)")
parser.add_argument("method", help="metoda meshowania (0=ball pivoting, 1=poisson, 2=alpha shapes)")
args = parser.parse_args()

nazwa = Path(args.filename).stem.split('.')[0]
katalog = Path(__file__).resolve().parent
katalog_chmury = (katalog / "chmury").resolve()
katalog_siatki = (katalog / "siatki").resolve()
katalog_nazwa = (katalog / "siatki" / f"{nazwa}").resolve()
model = (katalog / "chmury" / args.filename).resolve()
wyjscie = katalog_nazwa / f"{nazwa}.obj"
wyjscie_kolor_obj = katalog_nazwa / f"{nazwa}_kolor.obj"
wyjscie_kolor_ply = katalog_nazwa / f"{nazwa}_kolor.ply"

katalog_chmury.mkdir(exist_ok=True)
katalog_siatki.mkdir(exist_ok=True)
katalog_nazwa.mkdir(exist_ok=True)

metody = ['ball pivoting', 'poisson', 'alpha shapes']
print(f"Wybrano metodę: {metody[int(args.method)]}")
if not model.exists():
    print(f"Brak pliku: {model}")
    sys.exit(1)
else:
    print(f"Używam pliku: {model}")
czegoUzywac = int(args.method)


###wlasciwy kod

##wywalenie punktow z quality < cutoff
quality_cutoff = 0.7

wyjscieJakosciowe = katalog_nazwa / f"{nazwa}_quality.ply"

# Wczytaj PLY (header + dane)
with open(model) as f:
    linie = f.readlines()

# Znajdź koniec headera
header_end = 0
for i, l in enumerate(linie):
    if l.strip() == "end_header":
        header_end = i
        break

header = linie[:header_end+1]
data = np.loadtxt(linie[header_end+1:])

# data[:,9] to kolumna quality
mask = data[:, 9] >= quality_cutoff
filt_data = data[mask]

for i, line in enumerate(header):
    if line.startswith("element vertex"):
        przed = int(header[i].split()[2])
        header[i] = f"element vertex {filt_data.shape[0]}\n"
        po = int(header[i].split()[2])
        print(f"usunieto {przed-po} z oryginalych {przed} punktow z jakoscia < {quality_cutoff}")
        

with open(wyjscieJakosciowe, "w") as f:
    f.writelines(header)
    np.savetxt(f, filt_data, fmt="%f %f %f %f %f %f %d %d %d %f")

pcd_org = o3d.io.read_point_cloud(wyjscieJakosciowe)

# Sprawdzanie czy znajdzie kolorki
print("Zczytywanie kolorów z przefiltrowanej chmury...")
sa_kolory = False
og_kolorki = None
og_punkty = None

try:
    with open(wyjscieJakosciowe, 'r') as f:
        lines = f.readlines()
    
    vertex_count = 0
    slownik_wlasciwosci = {'x': -1, 'y': -1, 'z': -1, 'red': -1, 'green': -1, 'blue': -1}
    wlasciwosci = []
    numer_linii = 0

    for i, line in enumerate(lines):
        if 'element vertex' in line:
            vertex_count = int(line.split()[-1])
        elif 'property' in line:
            parts = line.strip().split()
            if len(parts) >= 3:
                nazwa_wlasciwosci = parts[2]
                wlasciwosci.append(nazwa_wlasciwosci)
                
                # Mapowanie nazw właściwości
                if nazwa_wlasciwosci == 'x':
                    slownik_wlasciwosci['x'] = len(wlasciwosci) - 1
                elif nazwa_wlasciwosci == 'y':
                    slownik_wlasciwosci['y'] = len(wlasciwosci) - 1
                elif nazwa_wlasciwosci == 'z':
                    slownik_wlasciwosci['z'] = len(wlasciwosci) - 1
                elif 'diffuse_red' in nazwa_wlasciwosci:
                    slownik_wlasciwosci['red'] = len(wlasciwosci) - 1
                elif 'diffuse_green' in nazwa_wlasciwosci:
                    slownik_wlasciwosci['green'] = len(wlasciwosci) - 1
                elif 'diffuse_blue' in nazwa_wlasciwosci:
                    slownik_wlasciwosci['blue'] = len(wlasciwosci) - 1
        elif 'end_header' in line:
            numer_linii = i + 1
            break

    if slownik_wlasciwosci['red'] >= 0 and slownik_wlasciwosci['green'] >= 0 and slownik_wlasciwosci['blue'] >= 0:
        print(f"Znaleziono kolory w przefiltrowanym PLY")
        
        kolorki = []
        vertices = []
        
        for i in range(numer_linii, numer_linii + vertex_count):
            if i >= len(lines):
                break
            parts = lines[i].strip().split()
            if len(parts) >= max(slownik_wlasciwosci['red'], slownik_wlasciwosci['green'], slownik_wlasciwosci['blue']) + 1:
                # Ekstrakcja kolorów, trzeba zmormalizować do [0;1]
                r = float(parts[slownik_wlasciwosci['red']]) / 255.0
                g = float(parts[slownik_wlasciwosci['green']]) / 255.0
                b = float(parts[slownik_wlasciwosci['blue']]) / 255.0
                kolorki.append([r, g, b])
                
                # Ekstrakcja pozycji
                x = float(parts[slownik_wlasciwosci['x']])
                y = float(parts[slownik_wlasciwosci['y']])
                z = float(parts[slownik_wlasciwosci['z']])
                vertices.append([x, y, z])
        
        if len(kolorki) > 0:
            og_kolorki = np.array(kolorki)
            og_punkty = np.array(vertices)
            sa_kolory = True
            print(f"Zczytano kolory z {len(og_kolorki)} punktów (próbka: {kolorki[0]})")
    
except Exception as e:
    print(f"Błąd podczas czytania kolorów z przefiltrowanego PLY: {e}")
    sa_kolory = False

#odszumienie przez usuniecie punktow z mala iloscia sasiadow
#samo to odszumienie tworzy nowa chmure punktow i wywala normalne ktore zrobil colmap, wieeec je zapisuje
points = np.asarray(pcd_org.points)
normals = np.asarray(pcd_org.normals)

if not pcd_org.has_normals():
    raise RuntimeError("Nie ma normalnych z colmapa!")

#trzeba sobie zadac pytanie jakich sasiadow usuwa
distances = pcd_org.compute_nearest_neighbor_distance() #czy to nie bedzie za dlugo sie liczyc????
avg_dist = np.mean(distances) #srednia odleglosc do sasiad
#to jakies takie heurystyki vvv
nb_neighbors = int(np.clip(20 / avg_dist, 10, 50)) #im gestsza chmura tym mniej sasiadow
std_ratio = np.clip(1.0 * avg_dist / 0.01, 0.8, 2.0) #im gestsza tym wieksze
pcd_filt, ind = pcd_org.remove_statistical_outlier(nb_neighbors=nb_neighbors, std_ratio=std_ratio) #i usuwanie, ind to indeksy tych ktore zostaly zeby dodac jeszcze normalne z colmapa a nie liczyc na nowo
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(points[ind])
pcd.normals = o3d.utility.Vector3dVector(normals[ind])

print(f"Po odszumieniu: {len(pcd.points)} punktów (było {len(pcd_org.points)})")
        
if czegoUzywac == 0:
    distances = pcd.compute_nearest_neighbor_distance()
    avg_dist = np.mean(distances)
    radius = 3 * avg_dist # Dr Florent Poux powiedzial ze spoko jest robić 3-krotność średniego dystansu między sąsiadami

    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
        pcd,
        o3d.utility.DoubleVector([radius, radius * 2]))

elif czegoUzywac == 1:
    normal_orientation_k = 30; #liczba sąsiadów używana do wymuszenia spójnej orientacji normalnych
    poisson_depth = 10; #glebokosc drzewa ?oktalnego? w poissonie
    density_quantile_threshold = 0.05; #tyle wierzcholkow o najmniejszej gestosci usunie
    # Niby spoko robić nwm
    pcd.orient_normals_consistent_tangent_plane(k=normal_orientation_k)
    
    # Rekonstrukcja poissona
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=poisson_depth, width=0, scale=1.1, linear_fit=False)
    
    # Czyszczenie tam gdzie jest mało więc w teorii można tego filtra używać na dense meshach
    if len(densities) > 0:
        vertices_to_remove = densities < np.quantile(densities, density_quantile_threshold)
        mesh.remove_vertices_by_mask(vertices_to_remove)

    mesh.remove_degenerate_triangles()
    mesh.remove_duplicated_triangles()
    mesh.remove_non_manifold_edges()
    mesh.compute_vertex_normals()

elif czegoUzywac == 2:
    distances = pcd.compute_nearest_neighbor_distance()
    avg_dist = np.mean(distances)
    alpha = 2.5 * avg_dist
    
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, alpha)

print(f"Vertices: {len(mesh.vertices)}")
print(f"Faces: {len(mesh.triangles)}")


o3d.io.write_triangle_mesh(str(wyjscie), mesh)

# Kolorowanie siatki
if sa_kolory and og_kolorki is not None and og_punkty is not None:
    print("\nPrzenoszenie kolorów do mesha...")
    
    try:
        # Budowanie drzewa z og punktów (po filtracji jakościowej)
        point_tree = cKDTree(og_punkty)

        # Szukanie najbliższego og punktu dla wierzchołka
        mesh_vertices = np.asarray(mesh.vertices)
        distances, indices = point_tree.query(mesh_vertices, k=1)
        
        # Przypisanie najbliższych kolorów do wierzchołków mesha
        mesh_colors = og_kolorki[indices]
        mesh.vertex_colors = o3d.utility.Vector3dVector(mesh_colors)
        
        print(f"Przeniesiono kolory do {len(mesh_colors)} wierzchołków")
        
        # Zapis kolorowego mesha
        print(f"Zapisywanie kolorowego mesha do: {wyjscie_kolor_obj}")
        o3d.io.write_triangle_mesh(str(wyjscie_kolor_obj), mesh, write_vertex_colors=True)
        o3d.io.write_triangle_mesh(str(wyjscie_kolor_ply), mesh, write_vertex_colors=True)
        
    except Exception as e:
        print(f"Błąd podczas przenoszenia kolorów: {e}")
        print("Używanie jednolitego koloru...")
        mesh.paint_uniform_color([0.5, 0.5, 0.5])
        # Czyszczenie plików jak nie wyjdzie
        for file_path in [wyjscie_kolor_obj, wyjscie_kolor_ply]:
            if file_path.exists():
                file_path.unlink()
else:
    print("\nBrak informacji o kolorach w przefiltrowanej chmurze - używanie jednolitego koloru")
    mesh.paint_uniform_color([0.5, 0.5, 0.5])
        # Czyszczenie plików jak nie wyjdzie
    for file_path in [wyjscie_kolor_obj, wyjscie_kolor_ply]:
        if file_path.exists():
            file_path.unlink()

# Aha bo to chyba i tak robiło z kolorami, chociaż nie wiem bo {nazwa}.obj w f3d jest tylko na szaro, a z kolorowaniem są kolorki więc chuj wie jak zrobiłem to i tak dodam
