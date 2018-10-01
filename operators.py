import bpy
import bmesh
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

def register():
    bpy.utils.register_class(AddSelectionMaskOperator)
    bpy.utils.register_class(VertexGroupFromSelection)
    bpy.utils.register_class(RemoveSelectionMaskOperator)
    bpy.utils.register_class(CollapsSelectionMaskOperator)

def unregister():
    bpy.utils.unregister_class(AddSelectionMaskOperator)
    bpy.utils.unregister_class(VertexGroupFromSelection)
    bpy.utils.unregister_class(RemoveSelectionMaskOperator)
    bpy.utils.unregister_class(CollapsSelectionMaskOperator)
