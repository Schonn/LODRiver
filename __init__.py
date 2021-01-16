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
        self.layout.operator('lodriver.createdrivers', text ='Create Visibility Drivers for Selected')
        self.layout.prop(context.scene,"LODRIVERSpacing",slider=False)

#function to add properties and drivers to selected objects to make them hide and show in renders and viewport based on distance to empty
class LODRIVER_OT_CreateDrivers(bpy.types.Operator):
    bl_idname = "lodriver.createdrivers"
    bl_label = "Create Visibility Drivers for Selected"
    bl_description = "Add a driver to the selected object that enables and disables visibility at certain distances from a reference object"
    
    def execute(self, context):
        print("create drivers")
        
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
            viewportDriver = lodObject.driver_add("hide_viewport").driver
            viewportDriverMaxVar = viewportDriver.variables.new()
            viewportDriverMaxVar.name = "LODRIVERMAX"
            viewportDriverMaxVar.targets[0].id = lodObject
            viewportDriverMaxVar.targets[0].data_path = '["LODRIVER_MAXDISTANCE"]'
            viewportDriverMinVar = viewportDriver.variables.new()
            viewportDriverMinVar.name = "LODRIVERMIN"
            viewportDriverMinVar.targets[0].id = lodObject
            viewportDriverMinVar.targets[0].data_path = '["LODRIVER_MINDISTANCE"]'
            viewportDriverDistanceToRefVar = viewportDriver.variables.new()
            viewportDriverDistanceToRefVar.name = "LODRIVERDISTTOREF"
            viewportDriverDistanceToRefVar.type = 'LOC_DIFF'
            viewportDriverDistanceToRefVar.targets[0].id = distanceReferenceEmpty
            viewportDriverDistanceToRefVar.targets[1].id = lodObject
            viewportDriver.expression = "LODRIVERDISTTOREF > LODRIVERMAX or LODRIVERDISTTOREF < LODRIVERMIN"
            renderDriver = lodObject.driver_add("hide_render").driver
            renderDriverCopyViewportVar = renderDriver.variables.new()
            renderDriverCopyViewportVar.name = "LODRIVERCOPYVIEWPORT"
            renderDriverCopyViewportVar.targets[0].id = lodObject
            renderDriverCopyViewportVar.targets[0].data_path = 'hide_viewport'
            renderDriver.expression = "LODRIVERCOPYVIEWPORT"

            
            print(lodObject.name)
        return {'FINISHED'}
             
#register and unregister all LOD River classes
lodriverClasses = (  LODRIVER_PT_LodPanel,
                    LODRIVER_OT_CreateDrivers)

register, unregister = bpy.utils.register_classes_factory(lodriverClasses)

#allow debugging for this addon in the Blender text editor
if __name__ == '__main__':
    register()
