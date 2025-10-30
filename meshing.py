import numpy as np
import open3d as o3d
import trimesh
from pathlib import Path
import os


base_dir = os.path.dirname(os.path.abspath(__file__))
prefix = os.path.join(base_dir, "undistort", "pmvs/") #colmap wyżej powinien go stworzyc
option_file = "slupek"#<- wewnatrz /undistort/pmvs 
model = option_file + ".ply"

pcd = o3d.io.read_point_cloud(os.path.join(prefix, "models/", model))
pcd.estimate_normals()

distances = pcd.compute_nearest_neighbor_distance()
avg_dist = np.mean(distances)
radius = 1.5 * avg_dist   

mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
           pcd,
           o3d.utility.DoubleVector([radius, radius * 2]))

# create the triangular mesh with the vertices and faces from open3d
# tri_mesh = trimesh.Trimesh(np.asarray(mesh.vertices), np.asarray(mesh.triangles),
#                           vertex_normals=np.asarray(mesh.vertex_normals))

# trimesh.convex.is_convex(tri_mesh)

o3d.visualization.draw_plotly([mesh])