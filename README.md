# Active LOD
Modal operator with start and stop menu to iterate through a Blender scene in chunks and automatically generate and swap LOD meshes based on the scale and distance to multiple reference empties.
The addon is accessed from the 'Active LOD' tab in object mode, clicking 'Start Active LOD' will create a default reference object and reference object collection if they do not already exist. It will then iterate the scene objects in chunks while creating and swapping mesh data as required.
Move and scale reference objects in the ACTLOD_REFERENCES collection to change nearby objects' LOD levels and the area of effect for the LOD change. An arbitrary number of references is possible.
Clicking 'Stop Active LOD' will stop scene iteration, mesh generation and mesh swapping.
Works when running with viewport rendering, likely to crash when used with proper rendering.
