import motmetrics as mm
import numpy as np
import os
import sacred
import time
import torch
import torchvision
import yaml

from os import path as osp
from sacred import Experiment
from torch.utils.data import DataLoader
from tqdm import tqdm

from tracktor.frcnn_fpn import FRCNN_FPN
from tracktor.config import get_output_dir
from tracktor.datasets.factory import Datasets
from tracktor.tracker import Tracker
from tracktor.reid.resnet import resnet50
from tracktor.utils import interpolate, plot_sequence, get_mot_accum, evaluate_mot_accums, plot_sequence_video
from libvott import Target

mm.lap.default_solver = 'lap'
os.environ["GIT_PYTHON_REFRESH"] = "quiet"

ex = Experiment()
ex.add_config('experiments/cfgs/tracktor.yaml')

# hacky workaround to load the corresponding configs and not having to hardcode paths here
ex.add_config(ex.configurations[0]._conf['tracktor']['reid_config'])

@ex.automain
def main(tracktor, reid, _config, _log, _run):
	target = Target()
	targetpath = target.Folder()
	targetname = target.TargetName()

	vottpath = target.GetVottPath()
	vottfile = target.GetVottContent()
	dictid, timelist = target.GetTagTime(vottfile)
	print(f"{len(timelist)} frames were tagged")

	timedict = target.ExtractByTimeList(timelist)
	bbdict = target.GetbbWithTime(vottfile)

	sacred.commands.print_config(_run)

	# set all seeds
	torch.manual_seed(tracktor['seed'])
	torch.cuda.manual_seed(tracktor['seed'])
	np.random.seed(tracktor['seed'])
	torch.backends.cudnn.deterministic = True

	output_dir = osp.join(get_output_dir(tracktor['module_name']), tracktor['name'])
	sacred_config = osp.join(output_dir, 'sacred_config.yaml')

	if not osp.exists(output_dir):
		os.makedirs(output_dir)
	with open(sacred_config, 'w') as outfile:
		yaml.dump(_config, outfile, default_flow_style=False)

	##########################
	# Initialize the modules #
	##########################

	# object detection
	_log.info("Initializing object detector.")

	obj_detect = FRCNN_FPN(num_classes=2)
	obj_detect.load_state_dict(torch.load(_config['tracktor']['obj_detect_model'],
							   map_location=lambda storage, loc: storage))

	obj_detect.eval()
	obj_detect.cuda()

	# reid
	reid_network = resnet50(pretrained=False, **reid['cnn'])
	reid_network.load_state_dict(torch.load(tracktor['reid_weights'],
								 map_location=lambda storage, loc: storage))
	reid_network.eval()
	reid_network.cuda()

	# tracktor
	print("Tracktor初始化完成")
	tracker = Tracker(obj_detect, reid_network, tracktor['tracker'])

	time_total = 0
	num_frames = 0
	mot_accums = []
	dataset = Datasets(tracktor['dataset'])

	for seq in dataset:
		tracker.reset()

		start = time.time()

		_log.info(f"Tracking: {seq}")

		data_loader = DataLoader(seq, batch_size=1, shuffle=False)
		print(f"{seq}加載完成, tracking開始")
		for i, frame in enumerate(tqdm(data_loader)):
			if len(seq) * tracktor['frame_split'][0] <= i <= len(seq) * tracktor['frame_split'][1]:
				id = tracker.step(frame, bbdict[timedict["%06d" % num_frames]])
				target.WriteID2asset(id, dictid[timedict["%06d" % num_frames]])
				num_frames += 1
		results = tracker.get_results()
		ids = list(results.keys())
		target.WriteID2vott(ids, vottfile=vottfile)

		time_total += time.time() - start

		_log.info(f"Tracks found: {len(results)}")
		_log.info(f"Runtime for {seq}: {time.time() - start :.1f} s.")

		target.CleanImg()

		if tracktor['interpolate']:
			results = interpolate(results)

		if seq.no_gt:
			_log.info(f"No GT data for evaluation available.")
		else:
			mot_accums.append(get_mot_accum(results, seq))

		_log.info(f"Writing predictions to: {output_dir}")
		seq.write_results(results, output_dir)

		if tracktor['write_images']:
			plot_sequence(results, seq, osp.join(output_dir, tracktor['dataset'], str(seq)))

		if tracktor['write_videos']:
			plot_sequence_video(results, seq, osp.join(output_dir, tracktor['dataset'], str(seq)))

	_log.info(f"Tracking runtime for all sequences (without evaluation or image writing): "
			  f"{time_total:.1f} s ({num_frames / time_total:.1f} Hz)")
	if mot_accums:
		evaluate_mot_accums(mot_accums, [str(s) for s in dataset if not s.no_gt], generate_overall=True)
