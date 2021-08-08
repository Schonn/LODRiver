# Active LOD Blender Addon
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
import math


#addon info read by Blender
bl_info = {
    "name": "Active LOD",
    "author": "Pierre",
    "version": (0, 0, 2),
    "blender": (2, 93, 1),
    "description": "Modal operator to replace LOD meshes based on distance to reference objects",
    "category": "Animation"
    }

#panel class for Active LOD Settings
class ACTLOD_PT_Settings(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'Active LOD Settings'
    bl_context = 'objectmode'
    bl_category = 'Active LOD'
    bpy.types.Scene.ACTLODStopSignal = bpy.props.BoolProperty(name="Stop Active LOD",description="Stop any currently running Active LOD operators",default=True)

    def draw(self, context):
        self.layout.operator('actlod.startactlod', text ='Start Active LOD')
        self.layout.operator('actlod.stopactlod', text ='Stop Active LOD')

#function to begin Active LOD
class ACTLOD_OT_StartActiveLod(bpy.types.Operator):
    bl_idname = "actlod.startactlod"
    bl_label = "Start Active LOD"
    bl_description = "Start Active LOD modal operator"
    
    #timer for running modal and settings for iterating through scene in chunks
    ACTLODTimer = None
    chunkIteration = 0
    chunkSizeMax = 10
    
    def setupCollection(self,context,newCollectionName):
        if(newCollectionName not in bpy.data.collections.keys()):
            bpy.ops.collection.create(name=newCollectionName)
            if(context.collection.name == "Master Collection"):
                bpy.context.scene.collection.children.link(bpy.data.collections[newCollectionName])
            else:
                bpy.data.collections[context.collection.name].children.link(bpy.data.collections[newCollectionName])
            return True
        else:
            return False

    def assignToCollection(self,context,assignCollectionName,assignObject):
        if(assignObject.name not in bpy.data.collections[assignCollectionName].objects):
            bpy.data.collections[assignCollectionName].objects.link(assignObject)
            if(context.collection.name == "Master Collection"):
                bpy.context.scene.collection.objects.unlink(assignObject)
            else:
                bpy.data.collections[context.collection.name].objects.unlink(assignObject)
    
    def modal(self, context, event):
        #stop modal timer if the stop signal is activated
        if(context.scene.ACTLODStopSignal == True):
            context.window_manager.event_timer_remove(self.ACTLODTimer)
            self.report({'INFO'},"Active LOD stopped.")
            return {'CANCELLED'}
        #set chunk size to max, or to the scene object list length if the scene is small
        chunkSizeAdjusted = self.chunkSizeMax
        if(chunkSizeAdjusted > len(bpy.context.scene.objects)):
            chunkSizeAdjusted = len(bpy.context.scene.objects)
        #iterate through scene objects in chunks
        for chunkStep in range(0,chunkSizeAdjusted):
            if(self.chunkIteration < len(bpy.context.scene.objects)):
                iterationObject = bpy.context.scene.objects[self.chunkIteration]
                #only work with meshes
                if(iterationObject.type == 'MESH'):
                    #measure distances and swap mesh data accordingly
                    shortestDistance = 999999
                    for distRefObject in bpy.data.collections['ACTLOD_REFERENCES'].objects:
                        measuredDistance = (distRefObject.matrix_world.translation-iterationObject.matrix_world.translation).length
                        measuredDistance = measuredDistance / abs(distRefObject.scale[0]+distRefObject.scale[1]+distRefObject.scale[2])
                        if(measuredDistance < shortestDistance):
                            shortestDistance = measuredDistance
                    #print(str(shortestDistance) + " distance for " + iterationObject.name)
                    #get desired lod level from distance
                    lodLevel = math.floor(shortestDistance)
                    if(lodLevel > 5):
                        lodLevel = 5
                    #set up LOD meshes if they do not exist
                    if(not(iterationObject.data.name.split('_LOD_')[0] + "_LOD_" + str(lodLevel) in bpy.data.meshes)):
                        if(iterationObject.data.name.split('_LOD_')[0] in bpy.data.meshes):
                            iterationObject.data = bpy.data.meshes[iterationObject.data.name.split('_LOD_')[0]]
                        lodTriangulate = iterationObject.modifiers.new('ACTLOD_TRIANGULATE','TRIANGULATE')
                        lodDecimate = iterationObject.modifiers.new('ACTLOD_DECIMATE','DECIMATE')
                        lodDecimate.ratio = 1 - (lodLevel * 0.2)
                        lodMeshData = bpy.data.meshes.new_from_object(iterationObject.evaluated_get(bpy.context.evaluated_depsgraph_get()))
                        lodMeshData.name = iterationObject.data.name.split('_LOD_')[0] + "_LOD_" + str(lodLevel)
                        iterationObject.modifiers.remove(lodDecimate)
                        iterationObject.modifiers.remove(lodTriangulate)
                        lodMeshData.use_fake_user = True
                    iterationObject.data = bpy.data.meshes[iterationObject.data.name.split('_LOD_')[0] + '_LOD_' + str(lodLevel)]
                self.chunkIteration += 1
            else:
                self.chunkIteration = 0
        #print(str(self.chunkIteration))
        return {'PASS_THROUGH'}

    def execute(self, context):
        if(context.scene.ACTLODStopSignal == True):
            context.scene.ACTLODStopSignal = False
            self.ACTLODTimer = context.window_manager.event_timer_add(0.1, window=context.window)
            context.window_manager.modal_handler_add(self)
            #if an ACTLOD references collection is new to the scene, add a LOD distance reference object to it
            if(self.setupCollection(context,'ACTLOD_REFERENCES') == True):
                bpy.ops.object.select_all(action='DESELECT')
                bpy.ops.object.empty_add(type='SPHERE')
                referenceObject = bpy.context.selected_objects[0]
                referenceObject.name = 'ACTLOD_DISTREF'
                self.assignToCollection(context,'ACTLOD_REFERENCES',referenceObject)
            self.report({'INFO'},"Active LOD started.")
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'},"Active LOD already running.")
            return {'FINISHED'}
        
        
#function to stop Active LOD
class ACTLOD_OT_StopActiveLod(bpy.types.Operator):
    bl_idname = "actlod.stopactlod"
    bl_label = "Stop Active LOD"
    bl_description = "Stop Active LOD modal operator"
    
    #turn on the stop signal switch
    def execute(self, context):
        context.scene.ACTLODStopSignal = True
        return {'FINISHED'}
    
#register and unregister all Active LOD classes
actlodClasses = (  ACTLOD_PT_Settings,
                    ACTLOD_OT_StartActiveLod,
                    ACTLOD_OT_StopActiveLod
                    )

register, unregister = bpy.utils.register_classes_factory(actlodClasses)

if __name__ == '__main__':
    register()
