# LOD River driver based viewport visibility Blender Addon
# Copyright (C) 2021 Pierre
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of  MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

#import blender python libraries
import bpy
import random
import math
import mathutils

#addon info read by Blender
bl_info = {
    "name": "LOD River",
    "author": "Pierre",
    "version": (0, 0, 1),
    "blender": (2, 91, 0),
    "description": "Quickly set up drivers that show and hide objects based on their distance from other objects",
    "category": "Object"
    }

#panel class for lod river menu items in object mode
class LODRIVER_PT_LodPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'LOD River'
    bl_context = 'objectmode'
    bl_category = 'LOD River'
    bpy.types.Scene.LODRIVERSpacing = bpy.props.FloatProperty(name="LOD Object Spacing",description="The amount of distance between a change in level of detail",default=10,min=0,max=90000)

    def draw(self, context):
        self.layout.operator('lodriver.parenttoempties', text ='Parent Selected Objects to Empties')
        self.layout.operator('lodriver.createdrivers', text ='Create Visibility Drivers for Selected')
        self.layout.prop(context.scene,"LODRIVERSpacing",slider=False)
        self.layout.operator('lodriver.visibleoverrideon', text ='Visible Override on Active Collection')
        self.layout.operator('lodriver.visibleoverrideoff', text ='No Visible Override on Active Collection')

#function to add properties and drivers to selected objects to make them hide and show in renders and viewport based on distance to empty
class LODRIVER_OT_CreateDrivers(bpy.types.Operator):
    bl_idname = "lodriver.createdrivers"
    bl_label = "Create Visibility Drivers for Selected"
    bl_description = "Add a driver to the selected object that enables and disables visibility at certain distances from a reference object"
    
    def execute(self, context):
        #store selected objects
        selectedObjects = bpy.context.selected_objects
        #create distance reference empty if it does not exist
        distanceReferenceEmpty = None
        lodSpacingDistance = context.scene.LODRIVERSpacing
        if not("LODRIVER_DISTREF_EMPTY" in bpy.context.scene.objects):
            bpy.ops.object.empty_add(type='PLAIN_AXES')
            distanceReferenceEmpty = bpy.context.selected_objects[0]
            distanceReferenceEmpty.name = "LODRIVER_DISTREF_EMPTY"
        else:
            distanceReferenceEmpty = bpy.context.scene.objects["LODRIVER_DISTREF_EMPTY"]
        #step through all selected objects to add drivers with increasing distances
        for lodObjectNumber in range(len(selectedObjects)):
            lodObject = selectedObjects[lodObjectNumber]
            lodObject["LODRIVER_MINDISTANCE"] = lodObjectNumber * lodSpacingDistance
            lodObject["LODRIVER_MAXDISTANCE"] = (lodObjectNumber * lodSpacingDistance) + lodSpacingDistance
            lodObject["LODRIVER_SWITCHOFF"] = 0
            viewportDriver = lodObject.driver_add("hide_viewport").driver
            viewportDriverMaxVar = viewportDriver.variables.new()
            viewportDriverMaxVar.name = "LODRIVERMAX"
            viewportDriverMaxVar.targets[0].id = lodObject
            viewportDriverMaxVar.targets[0].data_path = '["LODRIVER_MAXDISTANCE"]'
            viewportDriverMinVar = viewportDriver.variables.new()
            viewportDriverMinVar.name = "LODRIVERMIN"
            viewportDriverMinVar.targets[0].id = lodObject
            viewportDriverMinVar.targets[0].data_path = '["LODRIVER_MINDISTANCE"]'
            viewportDriverSwitchoff = viewportDriver.variables.new()
            viewportDriverSwitchoff.name = "LODRIVERSWITCHOFF"
            viewportDriverSwitchoff.targets[0].id = lodObject
            viewportDriverSwitchoff.targets[0].data_path = '["LODRIVER_SWITCHOFF"]'
            viewportDriverDistanceToRefVar = viewportDriver.variables.new()
            viewportDriverDistanceToRefVar.name = "LODRIVERDISTTOREF"
            viewportDriverDistanceToRefVar.type = 'LOC_DIFF'
            viewportDriverDistanceToRefVar.targets[0].id = distanceReferenceEmpty
            viewportDriverDistanceToRefVar.targets[1].id = lodObject
            viewportDriver.expression = "(LODRIVERDISTTOREF > LODRIVERMAX or LODRIVERDISTTOREF < LODRIVERMIN) and LODRIVERSWITCHOFF == 0"
            renderDriver = lodObject.driver_add("hide_render").driver
            renderDriverCopyViewportVar = renderDriver.variables.new()
            renderDriverCopyViewportVar.name = "LODRIVERCOPYVIEWPORT"
            renderDriverCopyViewportVar.targets[0].id = lodObject
            renderDriverCopyViewportVar.targets[0].data_path = 'hide_viewport'
            renderDriver.expression = "LODRIVERCOPYVIEWPORT"
        return {'FINISHED'}
    
#function to add empties at the origins of selected objects, then parent the objects to the empties
class LODRIVER_OT_ParentToEmpties(bpy.types.Operator):
    bl_idname = "lodriver.parenttoempties"
    bl_label = "Parent selected objects to empties"
    bl_description = "Add an empty at the origin of each selected object, then parent the object to that empty"
    
    def execute(self, context):
        #store selected objects
        selectedObjects = bpy.context.selected_objects
        #step through all selected objects to add empties and parent the objects to those empties
        for objectToParent in selectedObjects:
            bpy.ops.object.empty_add(type='PLAIN_AXES',location=objectToParent.location)
            parentEmpty = bpy.context.selected_objects[0]
            parentEmpty.name = "LODRIVER_TRANSFORM_" + objectToParent.name
            objectToParent.parent = parentEmpty
            objectToParent.matrix_parent_inverse
            objectToParent.location = (0,0,0)
        return {'FINISHED'}
    
#function to override drivers to make objects visible for easier duplication
class LODRIVER_OT_VisibleOverrideOn(bpy.types.Operator):
    bl_idname = "lodriver.visibleoverrideon"
    bl_label = "Turn on visibile override"
    bl_description = "Set a property so that the drivers for the active collection objects keep object visiblility on"
    
    def execute(self, context):
        #store collection objects
        collectionObjects = bpy.context.collection.objects
        #step through all objects in active collection to add empties and parent the objects to those empties
        for objectToMakeVisible in collectionObjects:
            if("LODRIVER_SWITCHOFF" in objectToMakeVisible):
                objectToMakeVisible["LODRIVER_SWITCHOFF"] = 1
        return {'FINISHED'}
    
#function to clear override from drivers
class LODRIVER_OT_VisibleOverrideOff(bpy.types.Operator):
    bl_idname = "lodriver.visibleoverrideoff"
    bl_label = "Turn off visibile override"
    bl_description = "Clear the override property on the active collection objects so the drivers switch LODs as expected"
    
    def execute(self, context):
        #store collection objects
        collectionObjects = bpy.context.collection.objects
        #step through all objects in active collection to add empties and parent the objects to those empties
        for objectToRevertLOD in collectionObjects:
            if("LODRIVER_SWITCHOFF" in objectToRevertLOD):
                objectToRevertLOD["LODRIVER_SWITCHOFF"] = 0
        return {'FINISHED'}
             
#register and unregister all LOD River classes
lodriverClasses = (  LODRIVER_PT_LodPanel,
                    LODRIVER_OT_CreateDrivers,
                    LODRIVER_OT_ParentToEmpties,
                    LODRIVER_OT_VisibleOverrideOn,
                    LODRIVER_OT_VisibleOverrideOff)

register, unregister = bpy.utils.register_classes_factory(lodriverClasses)

#allow debugging for this addon in the Blender text editor
if __name__ == '__main__':
    register()
