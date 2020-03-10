# vott_object_tracking
Automatically trace and ID the object labeled by VoTT

## Note
Please create two folders first  
    `Image`  
    `Video`

## Description
| program               | vott_object_tracking_iou          | vott_object_tracking_fpn                          |
| :--------------------:|-----------------------------------|---------------------------------------------------|
| Principle             | IOU + Distance + Relative position                | IOU + FPN + ResNet50                              |
| Applicable situation  | All                               | Sufficient light source, slow screen movement     |
| Hardware requirements | CPU                               | CPU + GPU ( VRAM > 3 GB )                         |
| Speed                 | Very fast                         | Slow                                              |
| Required files        | Target (.vott、.json)             | Video (.mp4)<br>Target (.vott、.json)             |
| Parameter preset      | Distance : 250<br>Preserve_gap : 2.0<Br>Backward : 5<br>Increase_dist : 20 | reid_sim_threshold : 1.1<br>reid_iou_threshold : 0|
| Note                  |                                   | Where applicable, the effect may be Better than vott_object_tracking_iou |
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
