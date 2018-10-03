import bpy
import bmesh
import numpy
from . parser import evaluate
from . conditions import getVariables
from bpy.props import IntProperty, StringProperty

def selectVertices(context):
    object = context.active_object
    mesh = bmesh.from_edit_mesh(object.data)
    variables = getVariables(object, mesh)
    result = evaluate(object.selection_expression, variables)
    for v, state in zip(mesh.verts, result):
        v.select = state
    bmesh.update_edit_mesh(object.data)

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

class UpdateSelectionMask(bpy.types.Operator):
    bl_idname = "mesh.update_selection_mask"
    bl_label = "Update Selection Mask"
    name = StringProperty()

    def execute(self, context):
        mesh = context.active_object.data
        bm = bmesh.from_edit_mesh(mesh)
        mesh[self.name] = numpy.fromiter(vert.select for vert in bm.verts, bool)
        return {'FINISHED'}

classes = [AddSelectionMaskOperator, VertexGroupFromSelection,
           RemoveSelectionMaskOperator, CollapsSelectionMaskOperator]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
