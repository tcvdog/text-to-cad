#!/usr/bin/env python3
"""Small STL mesh inspector using only the Python standard library."""
from __future__ import annotations

import math
import struct
import sys
from collections import Counter
from pathlib import Path


def _q(v: float, ndigits: int = 5) -> float:
    return round(v, ndigits)


def _key(pt: tuple[float, float, float]) -> tuple[float, float, float]:
    return (_q(pt[0]), _q(pt[1]), _q(pt[2]))


def _edge(a: tuple[float, float, float], b: tuple[float, float, float]):
    ka, kb = _key(a), _key(b)
    return (ka, kb) if ka <= kb else (kb, ka)


def read_stl(path: Path):
    data = path.read_bytes()
    if len(data) >= 84:
        tri_count = struct.unpack_from("<I", data, 80)[0]
        expected = 84 + tri_count * 50
        if expected == len(data):
            tris = []
            off = 84
            for _ in range(tri_count):
                vals = struct.unpack_from("<12fH", data, off)
                pts = (vals[3:6], vals[6:9], vals[9:12])
                tris.append(pts)
                off += 50
            return "binary", tris

    text = data.decode("utf-8", errors="ignore").splitlines()
    verts = []
    tris = []
    for line in text:
        parts = line.strip().split()
        if len(parts) == 4 and parts[0].lower() == "vertex":
            verts.append(tuple(float(x) for x in parts[1:4]))
            if len(verts) == 3:
                tris.append(tuple(verts))
                verts = []
    return "ascii", tris


def tri_area(tri) -> float:
    a, b, c = tri
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cross = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    return 0.5 * math.sqrt(cross[0] ** 2 + cross[1] ** 2 + cross[2] ** 2)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: inspect_stl_mesh.py MODEL.stl", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    kind, tris = read_stl(path)
    if not tris:
        print(f"ERROR: no triangles parsed from {path}")
        return 1

    xs, ys, zs = [], [], []
    edges = Counter()
    degenerate = 0
    area = 0.0
    vertices = set()

    for tri in tris:
        tri_area_value = tri_area(tri)
        area += tri_area_value
        if tri_area_value <= 1e-9:
            degenerate += 1
        for pt in tri:
            xs.append(pt[0])
            ys.append(pt[1])
            zs.append(pt[2])
            vertices.add(_key(pt))
        edges[_edge(tri[0], tri[1])] += 1
        edges[_edge(tri[1], tri[2])] += 1
        edges[_edge(tri[2], tri[0])] += 1

    boundary_edges = sum(1 for count in edges.values() if count == 1)
    nonmanifold_edges = sum(1 for count in edges.values() if count > 2)
    duplicate_edge_refs = sum(count - 2 for count in edges.values() if count > 2)

    print(f"path: {path}")
    print(f"format: {kind}")
    print(f"triangles: {len(tris)}")
    print(f"unique_vertices_rounded_1e-5: {len(vertices)}")
    print(f"surface_area_estimate: {area:.3f}")
    print(f"bounds_min: {min(xs):.3f}, {min(ys):.3f}, {min(zs):.3f}")
    print(f"bounds_max: {max(xs):.3f}, {max(ys):.3f}, {max(zs):.3f}")
    print(f"size: {max(xs) - min(xs):.3f}, {max(ys) - min(ys):.3f}, {max(zs) - min(zs):.3f}")
    print(f"center: {(max(xs) + min(xs)) / 2:.3f}, {(max(ys) + min(ys)) / 2:.3f}, {(max(zs) + min(zs)) / 2:.3f}")
    print(f"degenerate_triangles: {degenerate}")
    print(f"unique_edges: {len(edges)}")
    print(f"boundary_edges: {boundary_edges}")
    print(f"nonmanifold_edges: {nonmanifold_edges}")
    print(f"extra_nonmanifold_edge_refs: {duplicate_edge_refs}")
    print(f"watertight_by_edge_count: {boundary_edges == 0 and nonmanifold_edges == 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
