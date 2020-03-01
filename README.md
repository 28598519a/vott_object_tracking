# vott_object_tracking
Automatically trace and ID the object labeled by VoTT

## Note
Please create two folders first  
    `Image`  
    `Video`

## Description
| program               | vott_object_tracking_fpn                          | vott_object_tracking_iou       |
| :--------------------:|---------------------------------------------------|--------------------------------|
| Principle             | IOU + FPN + ResNet50                              | IOU + Distance                 |
| Applicable situation  | Sufficient light source, slow screen movement     | All                            |
| Hardware requirements | CPU + GPU ( VRAM > 3 GB )                         | CPU                            |
| Speed                 | Slow                                              | Very fast                      |
| Required files        | Video (.mp4)<br>Target (.vott、.json)             | Target (.vott、.json)          |
| Parameter preset      | reid_sim_threshold : 1.1<br>reid_iou_threshold : 0| Backward : 1<br>Distance : 200 |
| Note                  | Where applicable, the effect may be Better than vott_object_tracking_iou | If most objects in the frames are very large Intensive, please give priority to use ott_object_tracking_fpn |
<br>
If there is no specific reason, simply select vott_object_tracking_iou

## Usage
### vott_object_tracking_fpn  
Set Parameter  
Edit experiments\cfgs\tracktor.yaml  
`reid_sim_threshold`  
`reid_iou_threshold`  
Run  
`python experiments/scripts/vott_object_tracking_fpn.py`  
### vott_object_tracking_iou  
Set Parameter  
Edit experiments\scripts\vott_object_tracking_fpn.py  
`Distance`  
`Backward`  
Run  
`python experiments/scripts/vott_object_tracking_iou.py`
