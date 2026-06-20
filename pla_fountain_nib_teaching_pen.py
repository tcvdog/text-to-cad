#!/usr/bin/env python3
"""PLA-friendly one-piece teaching pen with a fountain-pen nib silhouette."""
from math import hypot

from build123d import *


HANDLE_LENGTH = 100.0
NIB_LENGTH = 20.0
HANDLE_WIDTH = 14.0
NIB_SHOULDER_WIDTH = 18.0
BODY_THICKNESS = 3.2
REAR_RADIUS = HANDLE_WIDTH / 2

TIP_SLOT_WIDTH = 0.95
INK_GROOVE_WIDTH = 1.25
INK_GROOVE_DEPTH = 0.85
BREATHER_HOLE_DIA = 5.5
DECORATIVE_GROOVE_WIDTH = 0.85
DECORATIVE_GROOVE_DEPTH = 0.45
HANG_HOLE_DIA = 4.5


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


def _cut_top_polygon(points, depth):
    with BuildSketch(Plane.XY.offset(BODY_THICKNESS / 2 + 0.01)) as groove:
        _make_closed_face(points)
    extrude(groove.sketch, amount=-(depth + 0.02), mode=Mode.SUBTRACT)


def gen_step():
    with BuildPart() as pen:
        # Handle remains simple and flat so a student printer can print it
        # without supports. The rounded tail is included in the 100 mm body.
        straight_handle = HANDLE_LENGTH - REAR_RADIUS
        with Locations((-straight_handle / 2, 0, 0)):
            Box(straight_handle, HANDLE_WIDTH, BODY_THICKNESS)
        with Locations((-straight_handle, 0, 0)):
            Cylinder(REAR_RADIUS, BODY_THICKNESS)

        # Fountain-pen nib silhouette: broad shoulders, leaf taper, and a small
        # blunt writing tip that survives PLA printing.
        with BuildSketch(Plane.XY):
            _make_closed_face(
                [
                    Vector(0.0, -HANDLE_WIDTH / 2),
                    Vector(2.2, -NIB_SHOULDER_WIDTH / 2),
                    Vector(8.5, -5.8),
                    Vector(15.8, -2.25),
                    Vector(NIB_LENGTH, -0.75),
                    Vector(NIB_LENGTH, 0.75),
                    Vector(15.8, 2.25),
                    Vector(8.5, 5.8),
                    Vector(2.2, NIB_SHOULDER_WIDTH / 2),
                    Vector(0.0, HANDLE_WIDTH / 2),
                ]
            )
        extrude(amount=BODY_THICKNESS / 2, both=True)

        # Exterior rounding, deliberately modest so the bottom stays printable.
        fillet(pen.edges().filter_by(Axis.Z), radius=0.65)

        # Breather hole and center slit: these are iconic steel-nib features,
        # enlarged so a 0.4 mm nozzle keeps them open.
        with Locations((7.2, 0, 0)):
            Cylinder(BREATHER_HOLE_DIA / 2, BODY_THICKNESS + 0.6, mode=Mode.SUBTRACT)
        with Locations((14.0, 0, 0)):
            Box(13.0, TIP_SLOT_WIDTH, BODY_THICKNESS + 0.6, mode=Mode.SUBTRACT)

        # Shallow ink feed groove running from the grip area into the breather
        # hole. This keeps the model useful as a dipped writing demo.
        with Locations((-14.0, 0, BODY_THICKNESS / 2 - INK_GROOVE_DEPTH / 2)):
            Box(30.0, INK_GROOVE_WIDTH, INK_GROOVE_DEPTH + 0.05, mode=Mode.SUBTRACT)

        # Nib decoration grooves, similar to stamped steel nib contour lines.
        _cut_top_polygon(_slot_polygon((1.5, -6.15), (12.8, -2.1), DECORATIVE_GROOVE_WIDTH), DECORATIVE_GROOVE_DEPTH)
        _cut_top_polygon(_slot_polygon((1.5, 6.15), (12.8, 2.1), DECORATIVE_GROOVE_WIDTH), DECORATIVE_GROOVE_DEPTH)
        _cut_top_polygon(_slot_polygon((3.4, -7.35), (9.2, -4.4), DECORATIVE_GROOVE_WIDTH), DECORATIVE_GROOVE_DEPTH)
        _cut_top_polygon(_slot_polygon((3.4, 7.35), (9.2, 4.4), DECORATIVE_GROOVE_WIDTH), DECORATIVE_GROOVE_DEPTH)

        # A small through-hole at the tail for hanging or labeling in class.
        with Locations((-94.0, 0, 0)):
            Cylinder(HANG_HOLE_DIA / 2, BODY_THICKNESS + 0.6, mode=Mode.SUBTRACT)

    result = pen.part
    result.label = "pla_fountain_nib_teaching_pen_0p4mm"
    return result

