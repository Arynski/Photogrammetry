import pycolmap
from pathlib import Path
import open3d as o3d
import numpy as np
import matplotlib as plt

n_watkow = 4 # Ile wątków
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
    database_path=output_dir/ "bazunia.db",
    image_path=zdjecia_dir,
    output_path=output_dir,
    options=pycolmap.IncrementalPipelineOptions(
      num_threads=n_watkow
    )
  )
  return rekonstrukcja

# Odpalajjj to

def main():
  rekonstrukcja = wlacz_rekonstrukcje(zdjecia_dir, output_dir)

  if rekonstrukcja is not None:

    rezultat = list(rekonstrukcja.values())[0]

    print(f"Zrekonstruowano coś!")
    print(f"Zarejestrowano {len(rezultat.images)} zdjęć")
    print(f"Utworzono {len(rezultat.points3D)} puntków 3D")
    rezultat.export_PLY(output_dir / "chmurka-cut.PLY")

  rekonstrukcja_dir = output_dir / "rekonstrukcja"
  rekonstrukcja_dir.mkdir(exist_ok=True)
  rezultat.write(output_dir / "rekonstrukcja")
  zaladowana_rekonstrukcja = pycolmap.Reconstruction(output_dir / "rekonstrukcja")

# main() TU JEST TA REKONSTRUKCJA COLMAP A NIZEJ ZABAWA open3d



def remove_small_connected_triangles(mesh, min_triangle_count=1000):
    labels = np.array(mesh.cluster_connected_triangles()[0])
    counts = np.bincount(labels)
    keep = np.where(counts[labels] >= min_triangle_count)[0]
    return mesh.select_by_index(keep)

ply_point_cloud = o3d.data.PLYPointCloud()
pcd_raw = o3d.io.read_point_cloud("./output/chmurka-cut.ply")


# cl, ind = pcd_raw.remove_statistical_outlier(nb_neighbors=30, std_ratio=1.0)
cl, ind = pcd_raw.remove_statistical_outlier(nb_neighbors=4, std_ratio=0.5)
pcd = pcd_raw.select_by_index(ind)

o3d.visualization.draw_plotly([pcd_raw])

alphamesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, 0.03)
alphamesh.compute_vertex_normals()
# o3d.visualization.draw_plotly([alphamesh])



distances = pcd.compute_nearest_neighbor_distance()
avg_dist = np.mean(distances)
radius = 6 * avg_dist
pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))



# bpa_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd, o3d.utility.DoubleVector([radius, 2* radius]))
poisson_mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=9)
# o3d.visualization.draw_plotly([bpa_mesh])
o3d.visualization.draw_plotly([poisson_mesh])

# dec_mesh = bpa_mesh.simplify_quadric_decimation(100000)
# dec_mesh.remove_degenerate_triangles()
# dec_mesh.remove_duplicated_triangles()
# dec_mesh.remove_duplicated_vertices()
# dec_mesh.remove_non_manifold_edges()

# o3d.visualization.draw_plotly([dec_mesh])