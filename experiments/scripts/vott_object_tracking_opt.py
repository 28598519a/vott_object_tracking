import cv2
import multiprocessing
import numpy
import os
import sys
root = os.path.join(sys.path[0], "..", "..")
sys.path.append(os.path.join(root, "src"))

from libvott import Target

Distance = 250
Preserve_gap = 2.0
Backward = 1
Tracking = True
Debug = False

def compute_iou(rec1, rec2):
	"""
	# param rec: (xmin, ymin, xmax, ymax)
	# return: scala value of IoU
	"""
	# computing area of each rectangles
	S_rec1 = (rec1[3] - rec1[1]) * (rec1[2] - rec1[0])
	S_rec2 = (rec2[3] - rec2[1]) * (rec2[2] - rec2[0])

	# computing the sum_area
	sum_area = S_rec1 + S_rec2

	# find the each edge of intersect rectangle
	left_line = max(rec1[0], rec2[0])
	right_line = min(rec1[2], rec2[2])
	top_line = max(rec1[1], rec2[1])
	bottom_line = min(rec1[3], rec2[3])

	# judge if there is an intersect
	if left_line >= right_line or top_line >= bottom_line:
		return 0
	else:
		intersect = (right_line - left_line) * (bottom_line - top_line)
		return (intersect / (sum_area - intersect)) * 1

def flowvec(img1, img2):
	def vec_avg(st1, ed1, st2, ed2):
		y, x = numpy.mgrid[st1:ed1:1, st2:ed2:1].reshape(2,-1).astype(int)
		fx, fy = flow[y,x].T
		lines = numpy.int32(numpy.vstack([x, y, x+fx, y+fy]).T.reshape(-1, 2, 2))
		tx1, tx2, ty1, ty2 = 0, 0, 0, 0
		for (x1,y1),(x2,y2) in lines:
			tx1 += x1
			tx2 += x2
			ty1 += y1
			ty2 += y2

		if len(lines) is not 0:
			vector = numpy.array([(tx2-tx1)/len(lines), (ty2-ty1)/len(lines)]).astype(int)
		else:
			vector = numpy.array([0,0])

		return vector

	gray_i = cv2.cvtColor(cv2.imread(img1), cv2.COLOR_BGR2GRAY)
	gray_k = cv2.cvtColor(cv2.imread(img2), cv2.COLOR_BGR2GRAY)

	flow = cv2.calcOpticalFlowFarneback(gray_i, gray_k, None, 0.5, 3, 15, 3, 5, 1.2, 0)

	h, w = gray_k.shape[:2]
	vec_lu = vec_avg(0, h/2, 0, w/2)
	vec_ru = vec_avg(0, h/2, w/2, w)
	vec_ld = vec_avg(h/2, h, 0, w/2)
	vec_rd = vec_avg(h/2, h, w/2, w)

	return vec_lu, vec_ru, vec_ld, vec_rd, h, w

def CalVec(xmin, ymin, vec_lu, vec_ru, vec_ld, vec_rd, h, w):
	if xmin < w/2:
		if ymin < h/2:
			vector = vec_lu
		else:
			vector = vec_ld
	else:
		if ymin < h/2:
			vector = vec_ru
		else:
			vector = vec_rd
	
	return tuple(vector)

def main():
	global Tracking
	i = 0
	track = 0
	id = {}

	target = Target(videodir="/home/czchen/stevenwork/data/NTUTAction/Videos", imagedir=os.path.join(root, "Image"))
	targetpath = target.Folder()
	targetname = target.TargetName()

	vottpath = target.GetVottPath()
	vottfile = target.GetVottContent()

	dictid, timelist = target.GetTagTime(vottfile)
	timelist = sorted(timelist, key = lambda x: float(x))
	print(f"{len(timelist)} frames were tagged")

	bbdict = target.GetbbWithTime(vottfile)
	timedict = target.ExtractByTimeList(timelist,extract = False)
	
	namelist = []
	for num in range(len(timelist)-1):
		namelist.append((os.path.join(target.imagedir, targetname, "%06d.jpg" % num), os.path.join(target.imagedir, targetname, "%06d.jpg" % (num+1))))
	
	with multiprocessing.Pool() as pool:
		vecout = pool.starmap(flowvec, namelist)

	while i != len(timelist):
		if i + 2 > len(timelist):
			Tracking = False
		boxes_i = [bb for bb in bbdict[timelist[i]]]

		if Tracking is True:
			vec_lu, vec_ru, vec_ld, vec_rd, h, w = vecout[i]

		if Debug is True:
			print()
			print(f"Time : {timelist[i]}")

		# All the boxes that this frame contains
		count = 0
		while i != len(timelist) and count != len(boxes_i):
			if i not in id.keys() or count not in id[i].keys():
				if i not in id.keys():
					id[i] = {}
				id[i][count] = track
				track += 1

			xmin = round(float(boxes_i[count][0]))
			ymin = round(float(boxes_i[count][1]))
			xmax = round(float(boxes_i[count][2]))
			ymax = round(float(boxes_i[count][3]))

			vector = CalVec(xmin, ymin, vec_lu, vec_ru, vec_ld, vec_rd, h, w)

			k = i + 1
			if Tracking is True and (float(timelist[k]) - float(timelist[i])) < Preserve_gap:
				boxes_k = [bb for bb in bbdict[timelist[k]]]

				listIOU = [compute_iou((xmin + vector[0], ymin + vector[1], xmax + vector[0], ymax + vector[1]), (round(float(boxes_k[j][0])), round(float(boxes_k[j][1])), round(float(boxes_k[j][2])),round(float(boxes_k[j][3])))) for j in range(len(boxes_k))]

				while True:
					matchIOU = [x for x in listIOU if x != 0]

					if Debug is True and len(matchIOU) > 1:
						print(f"Match IOU : {matchIOU}")

					index = listIOU.index(max(listIOU))

					if not (k in id.keys() and index in id[k].keys() and max(listIOU) != 0):
						break
					else:
						listIOU[index] = 0

				# Distnace point-to-point
				if max(listIOU) is 0:
					keep_break = 0

					for search in range(Backward):
						if keep_break is 1:
							break

						listp2p = [((xmin + vector[0] - round(float(boxes_k[j][0])))**2 + (ymin + vector[1] - round(float(boxes_k[j][1])))**2)**0.5 for j in range(len(boxes_k))]
						while True:
							matchp2p = [listp2p.index(x) for x in listp2p if x < Distance]
							if len(matchp2p) > 0:
								index = listp2p.index(min(listp2p))
							else:
								index = None
								if search != (Backward - 1) and (k + 1) < len(timelist) and (float(timelist[k+1]) - float(timelist[k])) < Preserve_gap:
									k += 1
									boxes_k = [bb for bb in bbdict[timelist[k]]]
									vec_lu, vec_ru, vec_ld, vec_rd, h, w = flowvec(os.path.join(target.imagedir, targetname, "%06d.jpg" % i), os.path.join(target.imagedir, targetname, "%06d.jpg" % k))
									vector = CalVec(xmin, ymin, vec_lu, vec_ru, vec_ld, vec_rd, h, w)
									break

							if not (k in id.keys() and index in id[k].keys()):
								keep_break = 1
								break
							else:
								listp2p[index] = Distance

			else:
				index = None

			if index != None:
				if k not in id.keys():
					id[k] = {}
				id[k][index] = id[i][count]

			count += 1

		if Debug is True:
			print(id[i])
		else:
			target.WriteID2asset(id[i], dictid[timelist[i]])

		i += 1
		print(f"\r{i} / {len(timelist)}", end="")

	if Debug is False:
		ids = [j for j in range(track)]
		target.WriteID2vott(ids, vottfile=vottfile)

	print()
	print(f"Tracks found: {track}")
	print('Done')
	
	target.CleanImg()

if __name__ == '__main__':
	main()
