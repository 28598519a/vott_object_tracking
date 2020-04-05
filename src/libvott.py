import json
import os
import re

class Target:
	targetpath = None
	targetname = None
	vottpath = None
	videodir = "Video"
	imagedir = "Image"

	def Folder(self):
		while True:
			Target.targetpath = input('Please write your target folder path( /home/.../Drone_XXX ) : ').replace("'","")
			if os.path.exists(Target.targetpath):
				break
			else:
				print("Target Path not exist")

		if not os.path.basename(Target.targetpath):
			Target.targetpath = Target.targetpath[:-1]

		return Target.targetpath

	def TargetName(self, target = None):
		if target is None:
			target = Target.targetpath
		Target.targetname = os.path.basename(target)

		return Target.targetname

	def Getcsv(self, target = None, targetname = None):
		if target is None:
			target = Target.targetpath
		if targetname is None:
			targetname = Target.targetname

		csvpath = os.path.join(target, "vott-csv-export", f"{targetname}-export.csv")
		if not os.path.exists(csvpath):
			raise OSError(f"{csvpath} not exist")

		print(f"Open {csvpath}")
		csvfile = open(csvpath, newline='')

		spiltcsv = csvfile.read()
		spiltcsv = spiltcsv.replace('"image","xmin","ymin","xmax","ymax","label"\n', "")
		spiltcsv = spiltcsv.replace('"', "")
		spiltcsv = spiltcsv.replace("'", "")

		csvfile.close()

		return spiltcsv

	def GetColumn(self, str, i):
		column = ""
		for row in str.split("\n"):
			column += row.split(',')[i] + "\n"

		return column

	def Csv2array(self, csvfile):
		row = csvfile.split("\n")
		array = [csvfile.split(',') for csvfile in row ]

		return array

	def OnlyTime(self, timelist):
		list = []
		for i in { i for i in timelist }:
			if i != "":
				list.append(float(i))

		return list

	def GetVottPath(self, target = None, targetname = None):
		if target is None:
			target = Target.targetpath
		if targetname is None:
			targetname = Target.targetname

		Target.vottpath = os.path.join(target, f"{targetname}.vott")
		if not os.path.exists(Target.vottpath):
			for file in os.listdir(target):
				if file.endswith(".vott"):
					Target.vottpath = os.path.join(target, file)
				else:
					raise OSError(f"{vottpath} not exist")

		return Target.vottpath

	def GetVottContent(self, vottpath = None):
		if vottpath is None:
			vottpath = Target.vottpath

		if not os.path.exists(vottpath):
			raise OSError(f"{vottpath} not exist")

		print(f"Open {vottpath}")
		file = open(vottpath, "r")
		vott = file.read()
		file.close()

		return vott

	def GetTagTime(self, vottfile):
		source = re.search(r'file:(.*?)#', vottfile).group(1)

		time = []
		dictid = {}
		vott = json.loads(vottfile)
		ID = list(vott["assets"].keys())
		for i in range(1, len(ID)):
			if vott["assets"][ID[i]]["state"] == 2:
				path = vott["assets"][ID[i]]["path"]
				path = path.replace("file:" + source, "")
				path = path.replace(f"#t=", "")
				time.append(float(path))
				dictid[float(path)] = ID[i]

		return dictid, time

	def GetbbWithTime(self, vottfile, target = None):
		if target is None:
			target = Target.targetpath

		source = re.search(r'file:(.*?)#', vottfile).group(1)

		bbdict = {}
		vott = json.loads(vottfile)
		ID = list(vott["assets"].keys())
		for i in range(1, len(ID)):
			if vott["assets"][ID[i]]["state"] == 2:
				path = vott["assets"][ID[i]]["path"]
				path = path.replace("file:" + source, "")
				path = path.replace("#t=", "")

				assetpath = os.path.join(target, ID[i] + "-asset.json")
				if os.path.exists(assetpath):
					jsonfile = open(assetpath, "r")
					asset = json.loads(jsonfile.read())
					jsonfile.close()

					for regions in asset["regions"]:
						if float(path) not in bbdict:
							bbdict[float(path)] = list()
						bbdict[float(path)].append([
							regions["boundingBox"]["left"],
							regions["boundingBox"]["top"],
							regions["boundingBox"]["left"] + regions["boundingBox"]["width"],
							regions["boundingBox"]["top"] + regions["boundingBox"]["height"]
						])
				else:
					print(f"Warning : {assetpath} not exist")

		return bbdict

	def GenNewID(self, data):
		m = hashlib.md5()
		m.update(data.encode("utf-8"))
		h = m.hexdigest()
		return h

	def WriteID2asset(self, id, assetid, target = None):
		if target is None:
			target = Target.targetpath

		assetpath = os.path.join(target, assetid + "-asset.json")
		if os.path.exists(assetpath):
			jsonfile = open(assetpath, "r")
			asset = json.loads(jsonfile.read())
			jsonfile.close()

			# JsonObject = dict ; jsonArray = list
			for i in range(len(asset["regions"])):
				asset["regions"][i]["tags"].insert(0,f"{id[i]}")

			jsonfile = open(assetpath, "w", newline="\n")
			jsonfile.write(json.dumps(asset, indent = 4))
			jsonfile.close()
		else:
			print(f"Warning : {assetpath} not exist")

	def WriteID2vott(self, ids, vottpath = None, vottfile = None):
		if vottpath is None:
			vottpath = Target.vottpath
		if vottfile is None:
			file = open(vottpath, "r")
			vottfile = file.read()
			file.close()

		if not os.path.exists(vottpath):
			raise OSError(f"{vottpath} not exist")

		colortable = ["#9D9D9D", "#FF0000", "#FF60AF", "#FF44FF", "#B15BFF", "#7D7DFF", "#46A3FF", "#4DFFFF", "#4EFEB3", "#53FF53", "#B7FF4A", "#FFFF37", "#FFDC35", "#FFAF60", "#FF8F59", "#AD5A5A", "#A5A552", "#5CADAD", "#8080C0", "#AE57A4"]

		key = ["name", "color"]

		vott = json.loads(vottfile)
		for i in range(len(ids)):
			value = [f"{ids[i]}", f"{colortable[i % 20]}"]
			vott["tags"].append(dict(zip(key, value)))

		file = open(vottpath, "w", newline="\n")
		file.write(json.dumps(vott, indent = 4))
		file.close()

	def DelVottVisitMark(self, vottpath = None, vottfile = None):
		if vottpath is None:
			vottpath = Target.vottpath
		if vottfile is None:
			file = open(vottpath, "r")
			vottfile = file.read()
			file.close()

		if not os.path.exists(vottpath):
			raise OSError(f"{vottpath} not exist")

		vott = json.loads(vottfile)
		ID = list(vott["assets"].keys())
		for i in range(1, len(ID)):
			if "predicted" in vott["assets"][ID[i]]:
				del vott["assets"][ID[i]]["predicted"]
			if vott["assets"][ID[i]]["state"] == 1:
				del vott["assets"][ID[i]]

		file = open(vottpath, "w")
		file.write(json.dumps(vott, indent = 4))
		file.close()

	def ExtractByTimeList(self, timelist, video = None, extract = True):
		# require opencv-python
		import cv2
		
		if video is None:
			video = os.path.join(Target.videodir, Target.targetname + ".mp4")
			targetname = Target.targetname
		else:
			targetname = os.path.splitext(video)[0]

		if not os.path.exists(video):
			raise OSError(f"{video} not exist")

		imgdir = os.path.join(Target.imagedir, targetname)
		if not os.path.exists(imgdir):
			os.mkdir(imgdir)

		timelist = sorted(timelist, key = lambda x: float(x))
		#print(timelist)
		filedict = {}
		listcount = len(timelist)

		if extract is True:
			video_capture = cv2.VideoCapture(video)
			count = 0
			filedict = {}
			print("Image extract start")
			while(video_capture.isOpened()):
				ret,frame = video_capture.read()
				timestamp = (video_capture.get(cv2.CAP_PROP_POS_MSEC))/1000

				if (ret == False and type(frame) is type(None)) or count == listcount:
					print("\nImage extract finish")
					break

				while timestamp >= timelist[count]:
					if timelist[count].is_integer():
						now = int(timelist[count])
					else:
						now = timelist[count]
					filedict["%06d" % count] = now
					n = os.path.join(imgdir, "%06d.jpg" % count)
					cv2.imwrite(n, frame)	  # save frame as JPEG file
					count += 1
					print(f"\r{count} / {listcount}", end="")
					break

			video_capture.release()
		else:
			for count in range(listcount):
				filedict["%06d" % count] = timelist[count]

		return filedict

	def CleanImg(self):
		# Return a normalized absolutized version of the pathname path, but does not represent existence.
		imgdir = os.path.abspath(Target.imagedir)
		if os.path.exists(imgdir):
			yn = input(f"Clean cache in {imgdir} ? (y/n)：")
			if yn == 'y':
				for root, dirs, files in os.walk(imgdir, topdown=False):
					for name in files:
						os.remove(os.path.join(root, name))
					for name in dirs:
						os.rmdir(os.path.join(root, name))
