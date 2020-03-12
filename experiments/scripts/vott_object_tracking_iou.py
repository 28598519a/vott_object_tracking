import os
import sys
sys.path.append(os.path.join(sys.path[0], "..", "..", "src"))

from libvott import Target

Distance = 250
Preserve_gap = 2.0
Backward = 3
Increase_dist = 20
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

def relate_match(boxes_i, boxes_k, match, st_point, Debug = False):
	offset = abs(len(boxes_i) - len(boxes_k))

	# calculate relative position of frame i
	LUi, RUi, LDi, RDi = 0, 0, 0, 0
	for x in range(0, len(boxes_i)):
		if x != st_point:
			if round(float(boxes_i[x][0])) > round(float(boxes_i[st_point][0])):
				if round(float(boxes_i[x][1])) > round(float(boxes_i[st_point][1])):
					LDi += 1
				else:
					LUi += 1
			else:
				if round(float(boxes_i[x][1])) > round(float(boxes_i[st_point][1])):
					RDi += 1
				else:
					RUi += 1

	# calculate relative position of frame k
	score = []
	for mh in match:
		LUk, RUk, LDk, RDk = 0, 0, 0, 0
		for x in range(0, len(boxes_k)):
			if x != mh:
				if round(float(boxes_k[x][0])) > round(float(boxes_k[mh][0])):
					if round(float(boxes_k[x][1])) > round(float(boxes_k[mh][1])):
						LDk += 1
					else:
						LUk += 1
				else:
					if round(float(boxes_k[x][1])) > round(float(boxes_k[mh][1])):
						RDk += 1
					else:
						RUk += 1

		# score is probably even
		score.append(abs(abs(LUi-LUk) + abs(RUi-RUk) + abs(LDi-LDk) + abs(RDi-RDk) - offset))

	if Debug is True:
		print("Relate score index and min :", score.index(min(score)), min(score))

	return match[score.index(min(score))]

def main():
	global Tracking, Distance
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
		if i + 2 > len(timelist):
			Tracking = False
		boxes_i = [bb for bb in bbdict[timelist[i]]]

		if Debug is True:
			print()
			print(f"Time : {timelist[i]}")

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
			if Tracking is True and (float(timelist[k]) - float(timelist[i])) < Preserve_gap:
				boxes_k = [bb for bb in bbdict[timelist[k]]]

				listIOU = [compute_iou((xmin, ymin, xmax, ymax), (round(float(boxes_k[j][0])), round(float(boxes_k[j][1])), round(float(boxes_k[j][2])),round(float(boxes_k[j][3])))) for j in range(len(boxes_k))]

				while True:
					matchIOU = [x for x in listIOU if x != 0]

					if Debug is True and len(matchIOU) > 1:
						print(f"Match IOU : {matchIOU}")

					if len(matchIOU) <= 1:
						index = listIOU.index(max(listIOU))
					else:
						matchIOU = [listIOU.index(x) for x in matchIOU]
						index = relate_match(boxes_i, boxes_k, matchIOU, count, Debug=Debug)

					if not (k in id.keys() and index in id[k].keys() and max(listIOU) != 0):
						break
					else:
						listIOU[index] = 0

				# Distnace point-to-point
				if max(listIOU) is 0:
					dist = Distance
					keep_break = 0

					for search in range(Backward):
						if keep_break is 1:
							break

						listp2p = [((xmin - round(float(boxes_k[j][0])))**2 + (ymin - round(float(boxes_k[j][1])))**2)**0.5 for j in range(len(boxes_k))]
						while True:
							matchp2p = [listp2p.index(x) for x in listp2p if x < Distance]
							if len(matchp2p) > 1 and search is 0:
								index = relate_match(boxes_i, boxes_k, matchp2p, count, Debug=Debug)
							elif len(matchp2p) is 1 or (search != 0 and len(matchp2p) > 0):
								index = listp2p.index(min(listp2p))
							else:
								index = None
								if search != (Backward - 1) and (k + 1) < len(timelist) and (float(timelist[k+1]) - float(timelist[k])) < Preserve_gap:
									Distance += Increase_dist
									k += 1
									boxes_k = [bb for bb in bbdict[timelist[k]]]
									break

							if not (k in id.keys() and index in id[k].keys()):
								keep_break = 1
								break
							else:
								listp2p[index] = Distance

					Distance = dist
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

	if Debug is False:
		ids = [j for j in range(track)]
		target.WriteID2vott(ids, vottfile=vottfile)

	print(f"Tracks found: {track}")
	print("Done")

if __name__ == '__main__':
	main()
