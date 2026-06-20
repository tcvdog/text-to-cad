#!/usr/bin/env python3
"""Curved fountain-nib teaching pen with fine slit and small breather hole.

The 0.2 mm slit and 0.5 mm breather hole are modeled as requested. On a
0.4 mm FDM nozzle, they may print closed and need post-print clearing.
"""
from math import hypot

from build123d import *


HANDLE_LENGTH = 100.0
NIB_LENGTH = 20.0
HANDLE_WIDTH = 14.0
NIB_SHOULDER_WIDTH = 18.0
BODY_THICKNESS = 3.2
REAR_RADIUS = HANDLE_WIDTH / 2

TIP_SLOT_WIDTH = 0.2
INK_GROOVE_WIDTH = 0.6
INK_GROOVE_DEPTH = 0.35
BREATHER_HOLE_DIA = 0.5
DECORATIVE_GROOVE_WIDTH = 0.45
DECORATIVE_GROOVE_DEPTH = 0.25
HANG_HOLE_DIA = 4.5
NIB_CROWN_RISE = 1.15


def _make_closed_face(points):
    with BuildLine() as outline:
        for index, point in enumerate(points):
            Line(point, points[(index + 1) % len(points)])
    make_face(outline.wires())


def _slot_polygon(start, end, width):
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    length = hypot(dx, dy)
    nx = -dy / length * width / 2
    ny = dx / length * width / 2
    return [
        Vector(sx + nx, sy + ny),
        Vector(ex + nx, ey + ny),
        Vector(ex - nx, ey - ny),
        Vector(sx - nx, sy - ny),
    ]


def _nib_width(x):
    t = max(0.0, min(1.0, x / NIB_LENGTH))
    if t < 0.15:
        return HANDLE_WIDTH + (NIB_SHOULDER_WIDTH - HANDLE_WIDTH) * (t / 0.15)
    return NIB_SHOULDER_WIDTH * (1.0 - (t - 0.15) / 0.85) + 1.35 * ((t - 0.15) / 0.85)


def _nib_section(x):
    width = _nib_width(x)
    top_base = BODY_THICKNESS / 2 - 0.15
    bottom = -BODY_THICKNESS / 2
    rise = NIB_CROWN_RISE * (1.0 - 0.18 * (x / NIB_LENGTH))
    pts = [(-width / 2, bottom)]
    for index in range(13):
        t = -1.0 + 2.0 * index / 12
        y = t * width / 2
        z = top_base + rise * (1.0 - t * t)
        pts.append((y, z))
    pts.append((width / 2, bottom))
    with BuildSketch(Plane.YZ.offset(x)) as section:
        with BuildLine():
            Polyline(*pts, close=True)
        make_face()
    return section.sketch


def _cut_top_polygon(points, depth):
    with BuildSketch(Plane.XY.offset(BODY_THICKNESS / 2 + NIB_CROWN_RISE + 0.03)) as groove:
        _make_closed_face(points)
    extrude(groove.sketch, amount=-(depth + NIB_CROWN_RISE + 0.1), mode=Mode.SUBTRACT)


def gen_step():
    with BuildPart() as pen:
        straight_handle = HANDLE_LENGTH - REAR_RADIUS
        with Locations((-straight_handle / 2, 0, 0)):
            Box(straight_handle, HANDLE_WIDTH, BODY_THICKNESS)
        with Locations((-straight_handle, 0, 0)):
            Cylinder(REAR_RADIUS, BODY_THICKNESS)

        # Curved nib body, lofted from broad shoulders to a narrow writing tip.
        loft([_nib_section(x) for x in (0.0, 4.0, 8.5, 14.5, NIB_LENGTH)], ruled=False)


        # Fine slit and small breather hole, as requested.
        with Locations((7.2, 0, 0.25)):
            Cylinder(BREATHER_HOLE_DIA / 2, BODY_THICKNESS + NIB_CROWN_RISE + 1.0, mode=Mode.SUBTRACT)
        with Locations((13.8, 0, 0.25)):
            Box(12.5, TIP_SLOT_WIDTH, BODY_THICKNESS + NIB_CROWN_RISE + 1.0, mode=Mode.SUBTRACT)

        # A narrow shallow ink groove on the top side, still visible in CAD.
        with Locations((-9.0, 0, BODY_THICKNESS / 2 - INK_GROOVE_DEPTH / 2)):
            Box(20.0, INK_GROOVE_WIDTH, INK_GROOVE_DEPTH + 0.05, mode=Mode.SUBTRACT)

        # Fine decorative nib lines.
        _cut_top_polygon(_slot_polygon((1.3, -6.1), (12.5, -2.0), DECORATIVE_GROOVE_WIDTH), DECORATIVE_GROOVE_DEPTH)
        _cut_top_polygon(_slot_polygon((1.3, 6.1), (12.5, 2.0), DECORATIVE_GROOVE_WIDTH), DECORATIVE_GROOVE_DEPTH)

        with Locations((-94.0, 0, 0)):
            Cylinder(HANG_HOLE_DIA / 2, BODY_THICKNESS + 0.6, mode=Mode.SUBTRACT)

    result = pen.part
    result.label = "pla_fountain_nib_curved_fine_pen_0p4mm"
    return result

