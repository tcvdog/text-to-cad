#!/usr/bin/env python3
"""Spur gear — 31 teeth, 30mm OD, 5mm face width, 8mm center bore.
All geometry centered on origin in XY and centered in Z.
"""
import math, time
from build123d import *

# ── Parameters ──────────────────────────────────────────────────────
N = 31
OD = 30.0
FACE_WIDTH = 5.0
BORE_DIA = 8.0
CENTERED = True  # Align to origin center

# ── Geometry ────────────────────────────────────────────────────────
m = OD / (N + 2)
PCD = m * N
OR = OD / 2
PR = PCD / 2
Rr = PR - 1.25 * m

t0 = time.time()

# Root cylinder (centered in Z)
root_cyl = Cylinder(radius=Rr, height=FACE_WIDTH, align=(Align.CENTER, Align.CENTER, Align.CENTER))
bore_cyl = Cylinder(radius=BORE_DIA / 2, height=FACE_WIDTH + 1, align=(Align.CENTER, Align.CENTER, Align.CENTER))
gear = root_cyl - bore_cyl

# One tooth shape (centered in Z)
tooth_angle = 2 * math.pi / N
thw = tooth_angle * 0.35  # Angular half-width at pitch circle

with BuildPart() as tp:
    with BuildSketch(Plane.XY) as sk:
        pts = [
            Vector(PR * math.cos(-thw), PR * math.sin(-thw)),
            Vector(OR * math.cos(-thw * 0.5), OR * math.sin(-thw * 0.5)),
            Vector(OR * math.cos(thw * 0.5), OR * math.sin(thw * 0.5)),
            Vector(PR * math.cos(thw), PR * math.sin(thw)),
        ]
        with BuildLine() as ln:
            for i in range(4):
                Line(pts[i], pts[(i + 1) % 4])
        make_face(ln.wires())
    extrude(amount=FACE_WIDTH / 2, both=True)  # Centered

tooth_shape = tp.part
# Rotate so first tooth center aligns with +X
tooth_shape = Rotation(0, 0, -tooth_angle / 2) * tooth_shape

# Fuse all teeth
for i in range(N):
    pos = Rotation(0, 0, i * tooth_angle) * tooth_shape
    gear = gear + pos

gear.label = "gear_31t"

build_time = time.time() - t0

# ── Export ──────────────────────────────────────────────────────────
export_step(gear, "gear_31t.step")
export_time = time.time() - t0 - build_time

print(f"gear_31t.step written")
print(f"Build: {build_time:.1f}s  Export: {export_time:.1f}s")
print(f"Teeth:{N}  OD:{OD}mm  Face:{FACE_WIDTH}mm  Bore:{BORE_DIA}mm")
print(f"Module:{m:.3f}  PCD:{PCD:.2f}mm  Rr:{Rr:.2f}mm")
