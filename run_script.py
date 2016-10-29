#!/usr/bin/env python
import argparse
import subprocess
import os
import threading
import csv
from datetime import datetime

class Run:
	def __init__(self):
		self.clean_thread = threading.Thread(target = self._run_make_clean)
		self.make_thread = threading.Thread(target = self._run_make)
		self.decode_thread = threading.Thread(target = self._run_decode)
		self.encode_thread = threading.Thread(target = self._run_encode)
		self.gprof_thread = threading.Thread(target = self._run_gprof)
		self.player_thread = threading.Thread(target = self._run_mplayer)
		self.csv_thread = threading.Thread(target = self._to_csv)

	def start(self):
		if Arguments.is_make() == True:
			self.clean_thread.start()
			self.clean_thread.join()
			self.make_thread.start()
			self.make_thread.join()
		if Arguments.is_decode() == True:
			self.decode_thread.daemon = False
			self.decode_thread.start()
			self.decode_thread.join()
		else:
			self.encode_thread.daemon = False
			self.encode_thread.start()
			self.encode_thread.join()
		self.gprof_thread.start()
		self.gprof_thread.join()
		self.csv_thread.start()
		self.csv_thread.join()		
		if Arguments.is_player():
			self.player_thread.daemon = True
			self.player_thread.start()
	def _run_make_clean(self): 
		print "cleaning make..."
		command = "make clean"
		make_clean_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid, 
			shell = True, bufsize = 1, cwd = (Arguments.get_directory() + "/build/linux"))
		while True:
			output = make_clean_process.stdout.readline()
			if output == '' and make_clean_process.poll() is not None:
				break
			if output:
				print output.strip()
		make_clean_process.stdout.flush()
	def _run_make(self):
		print "make..."
		command = "make"
		make_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid, 
			shell = True, bufsize = 1, cwd = (Arguments.get_directory() + "/build/linux"))
		while True:
			output = make_process.stdout.readline()
			if output == '' and make_process.poll() is not None:
				break
			if output:
				print output.strip()
		make_process.stdout.flush()
	def _run_decode(self):
		print "running decoder..."
		command = "./TAppDecoderStatic -b str.bin -o "+Arguments.get_yuv_file()
		decode_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid, 
			shell = True, bufsize = 1, cwd = (Arguments.get_directory() + "/bin"))
		while True:
			output = decode_process.stdout.readline()
			if output == '' and decode_process.poll() is not None:
				break
			if output:
				print output.strip()
		decode_process.stdout.flush()
	def _run_encode(self):
		print "running encoder..."
		command = "./TAppEncoderStatic -i " + Arguments.get_yuv_file() + " -wdt "+ str(Arguments.get_width())+" -hgt "+str(Arguments.get_height())+" -f " + str(Arguments.get_frames()) + " -fr 30 -c ../cfg/encoder_lowdelay_main.cfg"
		encode_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid, 
			shell = True, bufsize = 1, cwd = (Arguments.get_directory() + "/bin"))
		while True:
			output = encode_process.stdout.readline()
			if output == '' and encode_process.poll() is not None:
				break
			if output:
				print output.strip()
		encode_process.stdout.flush()
	def _run_gprof(self):
		print "running gprof"
		if Arguments.is_decode() == True:
			command = "gprof TAppDecoderStatic gmon.out > decode_output"
		else:
			command = "gprof TAppEncoderStatic gmon.out > encode_output"
		gprof_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid, 
			shell = True, bufsize = 1, cwd = (Arguments.get_directory() + "/bin"))
		while True:
			output = gprof_process.stdout.readline()
			if output == '' and gprof_process.poll() is not None:
				break
			if output:
				print output.strip()
		gprof_process.stdout.flush()
	def _to_csv(self):
		print "appending gprof info to " + Arguments.get_csv_file_name()
		global functionsList
		functionsList = []
		efile = open(os.path.join(Arguments.get_directory()+"/bin/", "encode_output"))
		lines = efile.readlines()  
		i = 5       #values start at 5th line in document (0,1,2,3,4,5)
		inDataTable = True
		while inDataTable == True:
			line = lines[i]
			if len(str(line[:53]).split()) == 6:
				functionDetails = str(line[:53]).split()
				functionDetails.append(line[54:])
				obj = EachFunction(functionDetails[6], float(functionDetails[0]), float(functionDetails[1]), float(functionDetails[2]), long(functionDetails[3]), float(functionDetails[4]), float(functionDetails[5]))
				functionsList.append(obj)
			if lines[i+1] == "/n" or len(lines[i+1].split()) == 0:   #signifies new line seperator of data in text file
				inDataTable = False
			i = i+1
		efile.close()

		data = [["" for i in xrange(len(functionsList)+1)] for i in xrange(6)] #creates matrix (number of functions (+1 for label) by number of characteristics)
		data[0][0] = "User- " + str(os.path.split(os.path.expanduser('~'))[-1])
		data[0][1] = "End Time- " + str(datetime.now())
		data[1][0] = "Function-Name:"
		data[2][0] = "Percent-Time:"
		data[3][0] = "Cumulative-Seconds:"
		data[4][0] = "Self-Seconds:"
		data[5][0] = "Calls:"

		i = 1
		while i <= len(functionsList):  
			data[1][i] = str(functionsList[i-1].getName())
			data[2][i] = str(functionsList[i-1].getPercentTime())
			data[3][i] = str(functionsList[i-1].getCumulativeSeconds())
			data[4][i] = str(functionsList[i-1].getSelfSeconds())
			data[5][i] = str(functionsList[i-1].getCalls())
			i = i + 1

		a_line = []
		a_line.append(" ")		
		with open(Arguments.get_csv_file_name(), "a") as csv_file:
			writer = csv.writer(csv_file, delimiter = ",")
			writer.writerows(a_line)
			writer.writerows(data)

	def _run_mplayer(self):
		print "starting mplayer"
		command = "mplayer rec.yuv -demuxer rawvideo -rawvideo w="+str(Arguments.get_width())+":h="+str(Arguments.get_height())
		mplayer_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid, 
			shell = True, bufsize = 1, cwd = (Arguments.get_directory() + "/bin"))
		while True:
			output = mplayer_process.stdout.readline()
			if output == '' and mplayer_process.poll() is not None:
				break
			if output:
				print output.strip()
		mplayer_process.stdout.flush()

class EachFunction:
	def __init__(self, name, percentTime, cumulativeSeconds, selfSeconds, calls, selfMSPerCall, totalMSPerCall):
		self.name = name
		self.percentTime = percentTime
		self.cumulativeSeconds = cumulativeSeconds
		self.selfSeconds = selfSeconds
		self.calls = calls
		self.selfMSPerCall = selfMSPerCall
		self.totalMSPerCall = totalMSPerCall

	def getName(self):
		return self.name

	def getPercentTime(self):
		return self.percentTime

	def getCumulativeSeconds(self):
		return self.cumulativeSeconds

	def getSelfSeconds(self):
		return self.selfSeconds

	def getCalls(self):
		return self.calls
    
	def getSelfMSPerCall(self):
		return self.selfMSPerCall

	def getTotalMSPerCall(self):
		return self.totalMSPerCall

class Arguments:
	def __init__(self):
		print ""
	@staticmethod
	def get_yuv_file():
		return args['yuv']
	@staticmethod
	def get_frames():
		if args['frames'] == None:
			return 10
		else:
			return args['frames']
	@staticmethod
	def is_decode():
		return args['yuv']
	@staticmethod
	def is_player():
		return args['player']
		print args['player']
	@staticmethod
	def get_width():
		if args['width'] == None:
			return 352
		else:
			return args['width']
	@staticmethod
	def get_height():
		if args['height'] == None:
			return 288
		else:
			return args['height']
	@staticmethod
	def get_directory():
		if args['dir'] == None:
			return str(os.path.dirname(os.path.realpath(__file__)))
		else:
			return args['dir']
	@staticmethod
	def is_make():
		return args['nomake']
	@staticmethod
	def get_csv_file_name():
		if args['csv'] == None:
			return "profiling_results.csv"
		else:
			return args['csv']

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-y','--yuv', help='give .yuv file; use quotes; gprof must be installed', required=True)
	parser.add_argument('-csv','--csv', help='set name of profiling csv file to be created or appended to in /bin (default is profiling_results.csv)', required=False)
	parser.add_argument('-nm','--nomake', help= 'do not run make or make clean', action = 'store_false', required = False)
	parser.add_argument('-d','--dir', help='set the directory of HM-9.0_org; use quotes (default is that run_script.py is located in HM-9.0_org folder)', required = False)
	parser.add_argument('-f', '--frames', help='set number of frames for encode (default is 10)', required = False)
	parser.add_argument('-dec', '--decode', help = '*beta, decode, flag (default is encode)',action = 'store_true', required = False)
	parser.add_argument('-p', '--player', help = '*beta play video afterwards, flag (must have mplayer, plays rec.yuv in /bin)',action = 'store_true', required = False)
	parser.add_argument('-wdt', '--width', help='set the resolution width (default is 352)', required = False) 
	parser.add_argument('-hgt', '--height', help='set the resolution height (default is 288)', required = False) 
	args = vars(parser.parse_args())
	obj = Arguments()
	obj = Run()
	obj.start()
	print "Done"