import bpy
from bpy.props import *
from . operators import selectVertices

selectionMaskTypes = [
    ("IN_RANGE", "In Range", "Vertices are in the given range", "NONE", 0),
    ("VERTEX_GROUP", "Vertex Group", "Use a custom vertex group", "NONE", 1),
    ("DIRECTION", "Direction", "The angles that vertices normals makes with the given vector are in a the given range", "NONE", 2)
]
rangeTypes = [
    ("MIN_MAX", "Min / Max", "Define range using maximum and minimum.", "NONE", 0),
    ("CENTER_SCALE", "Center/Scale", "Define range using center and scale.", "NONE", 1)
]

def autoUpdate(self, context):
    if context.active_object.auto_update:
        selectVertices(context)

class SelectionMaskOptions(bpy.types.PropertyGroup):
    name = StringProperty(update = autoUpdate)
    expanded = BoolProperty(default = True)
    type = EnumProperty(name = "Type", items = selectionMaskTypes, default = "IN_RANGE",
                        update = autoUpdate)
    invert = BoolProperty(name = "Invert", default = False)

    # Vertex Group.
    vertexGroupName = StringProperty(update = autoUpdate)

    # In Range.
    rangetype = EnumProperty(name = "Type", items = rangeTypes, default = "CENTER_SCALE",
                             update = autoUpdate)
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
                    drawMask(mask, object, box)
                elif mask.type == "IN_RANGE":
                    drawInRange(mask, object, box)
                elif mask.type == "DIRECTION":
                    drawDirection(mask, object, box)
                box.prop(mask, "invert", toggle = True)

        column.operator("mesh.add_selection_mask", text="", icon='PLUS')

        layout.separator()
        column = layout.column()
        column.label("Expression:")
        column.prop(object, "selection_expression", text="")
        row = column.row(True)
        row.operator("mesh.select_by_expression", text="Select")
        row.prop(object, "auto_update", text="", icon= "AUTO")

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

classes = [ObjectSelectPanel, SelectionMaskOptions]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.auto_update = BoolProperty(default = True)
    bpy.types.Object.selection_masks = CollectionProperty(type=SelectionMaskOptions)
    bpy.types.Object.selection_expression = StringProperty(update = autoUpdate,
                                                           options ={"TEXTEDIT_UPDATE"})

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Object.auto_update
    del bpy.types.Object.selection_masks
    del bpy.types.Object.selection_expression
