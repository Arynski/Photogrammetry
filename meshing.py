import numpy as np
import open3d as o3d
import trimesh
from pathlib import Path
import os
import argparse
import sys

#przyjmuje nazwe pliku ply, zakladamy ze jest w ./chmury
#i ktora metode wykorzystac (0=ball pivoting, 1=poisson, 2=alpha shapes)
parser = argparse.ArgumentParser()
parser.add_argument("filename", help="nazwa pliku PLY (sam plik, bez ścieżki)")
parser.add_argument("method", help="metoda meshowania (0=ball pivoting, 1=poisson, 2=alpha shapes)")
args = parser.parse_args()

katalog = Path(__file__).resolve().parent
model = (katalog / "chmury" / args.filename).resolve()
nazwa = Path(args.filename).stem.split('.')[0]
wyjscie = katalog / "chmury" / f"{nazwa}.obj"

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

wyjscieJakosciowe = katalog / "chmury" / f"{nazwa}_quality.ply"

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
pcd_filt, ind = pcd.remove_statistical_outlier(nb_neighbors=nb_neighbors, std_ratio=std_ratio) #i usuwanie, ind to indeksy tych ktore zostaly zeby dodac jeszcze normalne z colmapa a nie liczyc na nowo
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(points[ind])
pcd.normals = o3d.utility.Vector3dVector(normals[ind])
        
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
  alpha = 2.5 * np.mean(distances)
  
  mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, alpha)
  
print(f"Vertices: {len(mesh.vertices)}")
print(f"Faces: {len(mesh.triangles)}")

o3d.io.write_triangle_mesh(str(wyjscie), mesh)

# Wyświetlanie
o3d.visualization.draw_plotly([mesh])
