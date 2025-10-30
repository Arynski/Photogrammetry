import numpy as np
import open3d as o3d
import trimesh
from pathlib import Path
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
prefix = os.path.join(base_dir, "undistort", "pmvs/")
option_file = "slupek"
model = option_file + ".ply"

# Zmienna do wyboru metody (0=ball pivoting, 1=poisson, 2=alpha shapes)
czegoUzywac = 1

pcd = o3d.io.read_point_cloud(os.path.join(prefix, "models/", model))

if czegoUzywac == 1:
    print("Rekonstrukcja metodą poissona...")
    
    # Liczenie normalsów
    pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(
        radius=0.1, max_nn=30))
    
    # Niby spoko robić nwm
    pcd.orient_normals_consistent_tangent_plane(k=15)
    
    # Rekonstrukcja poissona
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=12, width=0, scale=1.1, linear_fit=False)
    
    # Czyszczenie tam gdzie jest mało więc w teorii można tego filtra używać na dense meshach
    if len(densities) > 0:
        vertices_to_remove = densities < np.quantile(densities, 0.1)
        mesh.remove_vertices_by_mask(vertices_to_remove)
    
elif czegoUzywac == 0:
    print("Rekonstrukcja metodą ball pivoting...")
    
    pcd.estimate_normals()
    
    distances = pcd.compute_nearest_neighbor_distance()
    avg_dist = np.mean(distances)
    radius = 3 * avg_dist # Dr Florent Poux powiedzial ze spoko jest robić 3-krotność średniego dystansu między sąsiadami
    
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
        pcd,
        o3d.utility.DoubleVector([radius, radius * 2]))
elif czegoUzywac == 2:
  print("Rekonstrukcja metodą alpha shapes")

  alpha = 0.1
  mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, alpha)
  

# Trimesh ze stackoverflow
tri_mesh = trimesh.Trimesh(
    vertices=np.asarray(mesh.vertices),
    faces=np.asarray(mesh.triangles),
    vertex_normals=np.asarray(mesh.vertex_normals) if mesh.has_vertex_normals() else None
)

# Czy jest wklęsły model nie wiem czemu sprawdzają
print(f"Is convex: {trimesh.convex.is_convex(tri_mesh)}")

# Czyszczenie
tri_mesh.fix_normals()
tri_mesh.update_faces(tri_mesh.unique_faces())

print(f"Statystyki:")
print(f"Vertices: {len(tri_mesh.vertices)}")
print(f"Faces: {len(tri_mesh.faces)}")

# Wyświetlanie
o3d.visualization.draw_plotly([mesh])