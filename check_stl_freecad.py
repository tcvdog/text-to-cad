#!/usr/bin/env python3
from pathlib import Path

import Mesh
import Part


path = Path("/home/tcvdog/桌面/text to cad/牛顿第一定律实验.STL")
mesh = Mesh.Mesh(str(path))

print(f"path: {path}")
print(f"facets: {mesh.CountFacets}")
print(f"points: {mesh.CountPoints}")
print(f"bbox: {mesh.BoundBox.XLength:.3f}, {mesh.BoundBox.YLength:.3f}, {mesh.BoundBox.ZLength:.3f}")
if hasattr(mesh, "isClosed"):
    print(f"closed: {mesh.isClosed()}")
if hasattr(mesh, "isSolid"):
    print(f"solid_mesh: {mesh.isSolid()}")

try:
    if hasattr(mesh, "getNonManifolds"):
        nonmanifolds = mesh.getNonManifolds()
        print(f"nonmanifold_edges: {len(nonmanifolds)}")
    else:
        print("nonmanifold_edges: unavailable")
except Exception as exc:
    print(f"nonmanifold_edges: unavailable ({exc})")

shape = Part.Shape()
shape.makeShapeFromMesh(mesh.Topology, 0.05)
print(f"shape_faces: {len(shape.Faces)}")
print(f"shape_shells: {len(shape.Shells)}")
print(f"shape_solids_before_solid: {len(shape.Solids)}")
print(f"shape_valid: {shape.isValid()}")
print(f"shape_closed: {shape.isClosed()}")

solid_ok = False
try:
    solid = Part.Solid(shape.Shells[0])
    solid_ok = solid.isValid() and len(solid.Solids) == 1
    print(f"solid_conversion_ok: {solid_ok}")
    print(f"solid_faces: {len(solid.Faces)}")
except Exception as exc:
    print(f"solid_conversion_ok: False ({exc})")

