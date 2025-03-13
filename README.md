## Dataset

This is a dataset named [CarlaRoad3D](https://huggingface.co/datasets/haonanmi/CarlaRoad3D/upload/main)
### Steps
1. Build and launch using the instructions above.
2. Click 'Load Scenes' in Menu/File
3. Click 'System Config' in Menu/Config.
4. Click "camera" at System_config Page, and set the FOV to the field of view of the camera taking the scene images. 
5. Click "model" at System_config page, and you can set the initial position, max position, position accuracy, size accuracy, scaling factor of the model.
   * initial position: The initial position of the model loaded into the scene.
   * max position: The position of the model in the scene closest to the camera. Moving the model beyond this position resets the model to its initial position during the move.
   * position accuracy: Display accuracy of model x,y,z position, located in 3DProperty module.
   * size accuracy: Display accuracy of model size(w, l, h), located in 3DProperty module.
   * scaling factor: Model movement speed in Z-axis.
6. Click the model name at Models module, and we can see the model loaded to its initial position.

   * If a model is selected and loaded as described above, if both model categories are the same, the new model will be loaded to the selected model location.
7. You can press the Shift key and press the left mouse button to select the model and move the mouse position to move the model in X and Y axis.
8. You can press the right mouse button to select the model and move the mouse position to move the model in the Z-axis.
9. In the visual perception of the human eye, object labeling is considered to be over when the model in the scene completely overlaps with the image object.

The annotation will be saved to the Scenes/<Your Scene>/annotations.

You can refer to the below hotkeys to speed up your workflow.  


### Hotkeys

| Hot key                  | Description                          |
| ------------------------ | ------------------------------------ |
| Ctrl + s                 | Save                                 |
| Ctrl + o                 | Load scenes                          |
| Ctrl + c                 | Copy model                           |
| Ctrl + v                 | Paste model                          |
| Ctrl + Space             | Copy Scene                           |
| 1                        | Previous image                       |
| Space                    | Next image                           |
| x                        | Delete Model                         |
| Shift + Left Mouse Button Move                        | Move the model along X, Y axis |
| Right Mouse Button Move | Move the model along Z axis |
| w                        | Rotate around the positive x-axis    |
| s                        |Rotate around the negative x-axis     |
| e                        | Rotate around the positive y-axis    |
| q                        |Rotate around the negative y-axis     |
| a                        | Rotate around the positive z-axis    |
| d                        |Rotate around the negative z-axis     |



### Label Annotations
The annotation files contain 3 main sections, as follows:  

Annotation.json  
├── image_file   [<sup>1</sup>](#R1): "images/0000.png"   
├── model  [<sup>2</sup>](#R2)  
│   ├── num  [<sup>3</sup>](#R3): 5  
│   ├── 0  [<sup>4</sup>](#R4)  
│   │   ├── model_file  [<sup>5</sup>](#R5): "models/Car.obj"  
│   │   ├── matrix: [0, …, ] 					# (16x1) matrix  [<sup>6</sup>](#R6)  
│   │   ├── R_matrix_c2o:[0, …, ] 				# (9x1) matrix  [<sup>7</sup>](#R7)  
│   │   ├── T_matrix_c2o:[0, …, ] 				# (3x1) matrix  [<sup>8</sup>](#R8)  
│   │   ├── 2d_bbox: [700, …, ]					# (4x1) matrix  [<sup>9</sup>](#R9)  
│   │   ├── 3d_bbox: [[721,500] …, ]			# (8x2) matrix  [<sup>10</sup>](#R10)  
│   │   ├── 3d_bbox_w: [[3.8, 2.4, 1.4],…，]		#(3x1) matrix  [<sup>11</sup>](#R11)  
│   │   ├── class: 1 							# object class num [<sup>12</sup>](#R12)  
│   │   ├── class_name: Car 					# object class name  [<sup>13</sup>](#R13)  
│   │   ├── size: [1.99, 1.55, 18.24]			# (3x1) matrix  [<sup>14</sup>](#R14)  
│   ├── 1[<sup>4</sup>](#R4)  
│   │   ├── model_file  [<sup>5</sup>](#R5): "models/Car.obj"  
│   │   ├── ......   
├── camera  [<sup>15</sup>](#R15)  
│   ├── matrix: [1.0, …, ] 						# (16x1) matrix  [<sup>16</sup>](#R16)  
│   ├── position: [0.0, 0.0, 0.52]				# (3x1) matrix  [<sup>17</sup>](#R17)  
│   ├── focalPoint: [0.0, 0.0, 0.0]				# (3x1) matrix  [<sup>18</sup>](#R18)  
│   ├── fov: 88.0								# camera fov  [<sup>18</sup>](#R18)  
│   ├── viewup: [0.0, 1.0, 0.0]					# camera viewup  [<sup>18</sup>](#R18)  
│   ├── distance: 0.52							# camera distance  [<sup>18</sup>](#R18)  

</br>

