bl_info = {
    "name": "Selection Logic",
    "description": "Advanced selections based on logical conditions.",
    "author": "Omar Ahmad",
    "version": (1, 0),
    "blender": (2, 79, 0),
    "location": "View3D",
    "warning": "",
    "category": "Mesh"
}

import bpy
import numpy
import bmesh
from bpy.props import *
from . import parse_expression

selectionMaskTypes = [
    ("VERTEX_GROUP", "Vertex Group", "Use a custom vertex group", "NONE", 0),
    ("IN_RANGE", "In Range", "Vertices are in the given range", "NONE", 1),
    ("DIRECTION", "Direction", "The angles that vertices normals makes with the given vector are in a the given range", "NONE", 2)
]
rangeTypes = [
    ("MIN_MAX", "Min / Max", "Define range using maximum and minimum.", "NONE", 0),
    ("CENTER_SCALE", "Center/Scale", "Define range using center and scale.", "NONE", 1)
]

def drawHeader(mask, box, index):
    row = box.row()
    row.operator("mesh.collapse_selection_mask", text="",
                icon='TRIA_DOWN' if mask.expanded else 'TRIA_RIGHT', emboss = False).index = index
    row.prop(mask, "name", text = "")
    row.operator("mesh.remove_selection_mask", text="", icon='X', emboss = False).index = index

def drawVertexGroup(mask, object, box):
    row = box.row(True)
    row.prop_search(mask, "vertexGroupName", object, "vertex_groups", text = "")
    row.operator("mesh.vertex_group_from_selection", text="", icon="UV_VERTEXSEL").name = mask.name

def drawInRange(mask, object, box):
    isMinMax = mask.rangetype == "MIN_MAX"
    box.prop(mask, "rangetype", text="")
    row = box.row()
    column = row.column()
    column.prop(mask, "minVector" if isMinMax else "centerVector")
    column = row.column()
    column.prop(mask, "maxVector" if isMinMax else "scaleVector")

def drawDirection(mask, object, box):
    isMinMax = mask.rangetype == "MIN_MAX"
    box.prop(mask, "direction", text="")
    box.prop(mask, "rangetype", text="")
    row = box.row(True)
    row.prop(mask, "minFloat" if isMinMax else "centerFloat")
    row.prop(mask, "maxFloat" if isMinMax else "scaleFloat")

class ObjectSelectPanel(bpy.types.Panel):
    bl_idname = "MESH_PT_selection_masks"
    bl_label = "Selection Masks"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "mesh_edit"

    def draw(self, context):
        layout = self.layout
        object = context.active_object

        column = layout.column()
        for index, mask in enumerate(object.selection_masks):
            box = column.box()
            drawHeader(mask, box, index)

            if mask.expanded:
                box.prop(mask, "type", text="")
                if mask.type == "VERTEX_GROUP":
                    drawVertexGroup(mask, object, box)
                elif mask.type == "IN_RANGE":
                    drawInRange(mask, object, box)
                elif mask.type == "DIRECTION":
                    drawDirection(mask, object, box)

        column.operator("mesh.add_selection_mask", text="", icon='PLUS')

        layout.separator()
        column = layout.column()
        column.label("Expression:")
        column.prop(object, "selection_expression", text="")
        row = column.row(True)
        row.operator("mesh.select_by_expression", text="Select")
        row.prop(object, "auto_update", text="", icon= "AUTO")

class AddSelectionMaskOperator(bpy.types.Operator):
    bl_idname = "mesh.add_selection_mask"
    bl_label = "Add Selection Mask"

    def execute(self, context):
        variables = "abcdefghijklmnopqrstuvwxyz"
        selectionMask = context.active_object.selection_masks.add()
        usedNames = [mask.name for mask in context.active_object.selection_masks]
        for var in variables:
            if var not in usedNames:
                selectionMask.name = var
                break
        return {'FINISHED'}

class RemoveSelectionMaskOperator(bpy.types.Operator):
    bl_idname = "mesh.remove_selection_mask"
    bl_label = "Remove Selection Mask"
    index = IntProperty()

    def execute(self, context):
        context.active_object.selection_masks.remove(self.index)
        return {'FINISHED'}

class CollapsSelectionMaskOperator(bpy.types.Operator):
    bl_idname = "mesh.collapse_selection_mask"
    bl_label = "Remove Selection Mask"
    index = IntProperty()

    def execute(self, context):
        mask = context.active_object.selection_masks[self.index]
        mask.expanded = False if mask.expanded else True
        return {'FINISHED'}

class VertexGroupFromSelection(bpy.types.Operator):
    bl_idname = "mesh.vertex_group_from_selection"
    bl_label = "Vertex Group From Selection"
    name = StringProperty()

    def execute(self, context):
        object = context.active_object
        object.vertex_groups.new(self.name)
        bpy.ops.object.vertex_group_assign()
        object.selection_masks[self.name].vertexGroupName = object.vertex_groups[-1].name
        return {'FINISHED'}

def inVertexGroup(object, name):
    vertexGroup = object.vertex_groups[name]
    verticesCount = len(object.data.vertices)
    weights = numpy.full(verticesCount, False)
    for i in range(verticesCount):
        try: weights[i] = (True, vertexGroup.weight(i))[0]
        except: pass
    return weights

def verticesInRangeMaxMin(mesh, min, max):
    result = numpy.full(len(mesh.verts), False)
    for i, vert in enumerate(mesh.verts):
        co = vert.co
        if ((co.x >= min.x) and (co.y >= min.y) and (co.z >= min.z) and
            (co.x <= max.x) and (co.y <= max.y) and (co.z <= max.z)):
            result[i] = True
    return result

def verticesInRangeCenterScale(object, center, scale):
    return verticesInRangeMaxMin(object, center - scale, center + scale)

def getVariables(object, mesh):
    variables = {}
    for mask in object.selection_masks:
        if mask.type == "VERTEX_GROUP":
            variables[mask.name] = inVertexGroup(object, mask.vertexGroupName)
        if mask.type == "IN_RANGE":
            if mask.rangetype == "MIN_MAX":
                variables[mask.name] = verticesInRangeMaxMin(mesh,
                                       mask.minVector, mask.maxVector)
            else:
                variables[mask.name] = verticesInRangeCenterScale(mesh,
                                       mask.centerVector, mask.scaleVector)
    return variables

def selectVertices(context):
    object = context.active_object
    mesh = bmesh.from_edit_mesh(object.data)
    variables = getVariables(object, mesh)
    result = parse_expression.evaluate(object.selection_expression, variables)
    for v, state in zip(mesh.verts, result):
        v.select = state
    bmesh.update_edit_mesh(object.data)

class SelectByExpressionOperator(bpy.types.Operator):
    bl_idname = "mesh.select_by_expression"
    bl_label = "Select By Expression"

    def execute(self, context):
        selectVertices(context)
        return {'FINISHED'}

def autoUpdate(self, context):
    if context.active_object.auto_update:
        selectVertices(context)

class SelectionMaskOptions(bpy.types.PropertyGroup):
    name = StringProperty(update = autoUpdate)
    expanded = BoolProperty(default = True)
    type = EnumProperty(name = "Type", items = selectionMaskTypes, default = "VERTEX_GROUP",
                        update = autoUpdate)

    # Vertex Group.
    vertexGroupName = StringProperty(update = autoUpdate)

    # In Range.
    rangetype = EnumProperty(name = "Type", items = rangeTypes, update = autoUpdate)
    minVector = FloatVectorProperty(name = "Min", subtype = "XYZ", update = autoUpdate)
    maxVector = FloatVectorProperty(name = "Max", subtype = "XYZ", update = autoUpdate)
    centerVector = FloatVectorProperty(name = "Center", subtype = "XYZ", update = autoUpdate)
    scaleVector = FloatVectorProperty(name = "Scale", subtype = "XYZ", update = autoUpdate)

    # Direction.
    direction = FloatVectorProperty(subtype = "DIRECTION", default=(0,0,1), update = autoUpdate)
    minFloat = FloatProperty(name = "Min", update = autoUpdate)
    maxFloat = FloatProperty(name = "Max", update = autoUpdate)
    centerFloat = FloatProperty(name = "Center", update = autoUpdate)
    scaleFloat = FloatProperty(name = "Scale", update = autoUpdate)

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Object.auto_update = BoolProperty()
    bpy.types.Object.selection_expression = StringProperty(update = autoUpdate,
                                            options ={"TEXTEDIT_UPDATE"})
    bpy.types.Object.selection_masks = CollectionProperty(type=SelectionMaskOptions)

def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Object.auto_update
    del bpy.types.Object.selection_masks
    del bpy.types.Object.selection_expression
