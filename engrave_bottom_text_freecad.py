#!/usr/bin/env python3
from pathlib import Path

import FreeCAD as App
import Mesh
import Part
import Draft
import MeshPart


TEXT = "北京师范大学亚太实验学校"
FONT = "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
INPUT = Path("/home/tcvdog/桌面/text to cad/牛顿第一定律实验.STL")
OUTPUT_STL = Path("/home/tcvdog/桌面/text to cad/牛顿第一定律实验_底部凹刻.stl")
OUTPUT_STEP = Path("/home/tcvdog/桌面/text to cad/牛顿第一定律实验_底部凹刻.step")

TEXT_HEIGHT = 12.0
TRACKING = 0.0
ENGRAVE_DEPTH = 0.8
CUT_EXTRA = 0.3


def solid_from_mesh(mesh: Mesh.Mesh):
    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh.Topology, 0.05)
    if not shape.Shells:
        raise RuntimeError("mesh conversion produced no shell")
    solid = Part.Solid(shape.Shells[0])
    if not solid.isValid():
        raise RuntimeError("converted solid is not valid")
    return solid


def make_text_shape(doc):
    text_obj = Draft.make_shapestring(TEXT, FONT, Size=TEXT_HEIGHT, Tracking=TRACKING)
    doc.recompute()
    shape = text_obj.Shape.copy()
    if shape.isNull():
        raise RuntimeError("FreeCAD produced an empty text shape")
    return shape


def main():
    doc = App.newDocument("engrave_bottom_text")
    mesh = Mesh.Mesh(str(INPUT))
    base_solid = solid_from_mesh(mesh)
    bbox = base_solid.BoundBox

    text_shape = make_text_shape(doc)
    text_bbox = text_shape.BoundBox
    available_x = bbox.XLength - 16.0
    if text_bbox.XLength > available_x:
        scale = available_x / text_bbox.XLength
        matrix = App.Matrix()
        matrix.scale(scale, scale, scale)
        text_shape = text_shape.transformGeometry(matrix)
        text_bbox = text_shape.BoundBox

    # Center the inscription on the bottom face and orient it so the engraving
    # cutter starts just below Z-min and cuts upward into the model.
    target_x = bbox.XMin + bbox.XLength / 2.0
    target_y = bbox.YMin + bbox.YLength / 2.0
    tx = target_x - (text_bbox.XMin + text_bbox.XLength / 2.0)
    ty = target_y - (text_bbox.YMin + text_bbox.YLength / 2.0)
    tz = bbox.ZMin - CUT_EXTRA
    text_shape.translate(App.Vector(tx, ty, tz - text_bbox.ZMin))

    cut_depth = ENGRAVE_DEPTH + CUT_EXTRA
    text_faces = []
    for wire in text_shape.Wires:
        try:
            face = Part.Face(wire)
            if face.Area > 0:
                text_faces.append(face)
        except Exception:
            pass
    if not text_faces:
        raise RuntimeError("no closed text faces could be created")

    cutters = []
    for face in text_faces:
        cutter = face.extrude(App.Vector(0, 0, cut_depth))
        if cutter.Volume > 0:
            cutters.append(cutter)
    if not cutters:
        raise RuntimeError("no text cutter solids could be extruded")

    cutter_compound = Part.makeCompound(cutters)
    engraved = base_solid.cut(cutter_compound)
    if not engraved.isValid():
        raise RuntimeError("engraved solid is not valid after boolean cut")

    Part.export([engraved], str(OUTPUT_STEP))

    mesh_out = MeshPart.meshFromShape(
        Shape=engraved,
        LinearDeflection=0.15,
        AngularDeflection=0.35,
        Relative=False,
    )
    mesh_out.write(str(OUTPUT_STL))

    print(f"input: {INPUT}")
    print(f"output_stl: {OUTPUT_STL}")
    print(f"output_step: {OUTPUT_STEP}")
    print(f"text: {TEXT}")
    print(f"font: {FONT}")
    print(f"engrave_depth_mm: {ENGRAVE_DEPTH}")
    print(f"bbox_mm: {bbox.XLength:.3f}, {bbox.YLength:.3f}, {bbox.ZLength:.3f}")
    print(f"text_bbox_after_scale_mm: {text_bbox.XLength:.3f}, {text_bbox.YLength:.3f}, {text_bbox.ZLength:.3f}")
    print(f"valid: {engraved.isValid()}")


if __name__ == "__main__":
    main()
