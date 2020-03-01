import cv2
import os
import sys
sys.path.append(os.path.abspath(os.path.join("..", "..", "src")))

from libvott import Target

Backward = 1
Distance = 200
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

def main():
	global Tracking
	i = 0
	track = 0
	id = {}
	
	target = Target()
	targetpath = target.Folder()
	targetname = target.TargetName()

	vottpath = target.GetVottPath()
	vottfile = target.GetVottContent()
	
	bbdict = target.GetbbWithTime(vottfile)
	dictid, timelist = target.GetTagTime(vottfile)
	timelist = sorted(timelist, key = lambda x: float(x))
	print(f"{len(timelist)} frames were tagged")

	while i != len(timelist):
		if i + 1 >= (len(timelist) - 1):
			Tracking = False
		boxes_i = [bb for bb in bbdict[timelist[i]]]

		# Draw all the boxes that this frame contains
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
			
			k = i + 1
			if Tracking is True and (float(timelist[k]) - float(timelist[i])) < 0.2:
				boxes_k = [bb for bb in bbdict[timelist[k]]]
				
				listIOU = [compute_iou((xmin, ymin, xmax, ymax), (round(float(boxes_k[j][0])), round(float(boxes_k[j][1])), round(float(boxes_k[j][2])),round(float(boxes_k[j][3])))) for j in range(len(boxes_k))]
				index = listIOU.index(max(listIOU))
				
				while k in id.keys() and index in id[k].keys() and max(listIOU) != 0:
					listIOU[index] = 0
					index = listIOU.index(max(listIOU))

				# Distnace point-to-point
				if max(listIOU) == 0:
					for search in range(Backward):
						listp2p = [((xmin - round(float(boxes_k[j][0])))**2 + (ymin - round(float(boxes_k[j][1])))**2)**0.5 for j in range(len(boxes_k))]
						if min(listp2p) < Distance:
							index = listp2p.index(min(listp2p))
							
							while k in id.keys() and index in id[k].keys():
								listp2p[index] = Distance
								index = listp2p.index(min(listp2p))
								if min(listp2p) >= Distance:
									index = None
									if search != (Backward - 1):
										if k < (len(timelist) - 1) and (float(timelist[k+1]) - float(timelist[k])) < 0.2:
											k += 1
											boxes_k = [bb for bb in bbdict[timelist[k]]]
									break
						else:
							index = None
			else:
				index = None
			
			if index != None:
				if k not in id.keys():
					id[k] = {}
				id[k][index] = id[i][count]
			
			count += 1

		if Debug is True:
			print(id[i])
			input()
		
		target.WriteID2asset(id[i], dictid[timelist[i]])
		i += 1

	ids = [j for j in range(track)]
	target.WriteID2vott(ids, vottfile=vottfile)
	
	print(f"Tracks found: {track}")
	print("Done")

if __name__ == '__main__':
	main()
