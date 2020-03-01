import configparser
import csv
import cv2
import numpy as np
import os
import os.path as osp
import torch

from PIL import Image
from torch.utils.data import Dataset
from torchvision.transforms import ToTensor

from ..config import cfg

class NTUT_Sequence(Dataset):
    """Multiple Object Tracking Dataset.

    This dataloader is designed so that it can handle only one sequence, if more have to be
    handled one should inherit from this class.
    """

    def __init__(self, seq_name=None, dets='', vis_threshold=0.0,
                 normalize_mean=[0.485, 0.456, 0.406],
                 normalize_std=[0.229, 0.224, 0.225]):
        """
        Args:
            seq_name (string): Sequence to take
            vis_threshold (float): Threshold of visibility of persons above which they are selected
        """
        self._seq_name = seq_name
        self._dets = dets
        self._vis_threshold = vis_threshold
        self.transforms = ToTensor()
        self.data, self.no_gt = self._sequence()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        """Return the ith image converted to blob"""
        data = self.data[idx]
        img = Image.open(data['im_path']).convert("RGB")
        img = self.transforms(img)

        sample = {}
        sample['img'] = img
        sample['img_path'] = data['im_path']

        return sample

    def _sequence(self):
        
        dir = '/home/ntut-drone/NTUTAction/Image'
        
        self.imDir = osp.join(dir, self._seq_name)
        seqLength = len([name for name in os.listdir(self.imDir) if os.path.isfile(osp.join(self.imDir, name))])

        total = []
        train = []
        val = []

        visibility = {}
        boxes = {}
        dets = {}

        for i in range(1, seqLength+1):
            boxes[i] = {}
            visibility[i] = {}
            dets[i] = []
        
        no_gt = True
        
        det_file = ""

        if osp.exists(det_file):
            with open(det_file, "r") as inf:
                reader = csv.reader(inf, delimiter=',')
                for row in reader:
                    x1 = float(row[2]) - 1
                    y1 = float(row[3]) - 1
                    # This -1 accounts for the width (width of 1 x1=x2)
                    x2 = x1 + float(row[4]) - 1
                    y2 = y1 + float(row[5]) - 1
                    score = float(row[6])
                    bb = np.array([x1,y1,x2,y2, score], dtype=np.float32)
                    dets[int(row[0])].append(bb)
        files = [os.path.join(self.imDir, f) for f in os.listdir(self.imDir) if os.path.isfile(os.path.join(self.imDir, f))]
        
        files = sorted(files)
        for im_path in files:
            sample = {'gt':None,
                      'im_path':im_path,
                      'vis':None,
                      'dets':None,}

            total.append(sample)

        return total, no_gt


    def __str__(self):
        return str(self._seq_name)

    def write_results(self, all_tracks, output_dir):
        """Write the tracks in the format for MOT17 sumbission

        all_tracks: dictionary with 1 dictionary for every track with {..., i:np.array([x1,y1,x2,y2]), ...} at key track_num

        Each file contains these lines:
        <frame>, <id>, <bb_left>, <bb_top>, <bb_width>, <bb_height>

        Files to sumbit:
        ./{name}.txt
        """

        assert self._seq_name is not None, "[!] No seq_name, probably using combined database"

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        file = osp.join(output_dir, self._seq_name +'.log')

        with open(file, "w") as of:
            writer = csv.writer(of, delimiter=',')
            for i, track in all_tracks.items():
                for frame, bb in track.items():
                    x1 = bb[0]
                    y1 = bb[1]
                    x2 = bb[2]
                    y2 = bb[3]
                    # frame,track_id,x,y,w,h ;    frame start from 1
                    writer.writerow([frame+1, i+1, x1+1, y1+1, x2-x1+1, y2-y1+1])
