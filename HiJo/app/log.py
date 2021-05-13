from datetime import datetime, timedelta
import time
import os
import os.path
import collections

import settings

logPath = "logs"

def checkFolder():
	try:
		# Creating log folder if it does not exist
		path = os.path.join(settings.appDir, logPath)
		if not os.path.exists(path):
			os.mkdir(path)
			print("Log: folder created")
	except Exception as ex:
		print("Log: Error:", str(ex))
	pass

def currentFilename(timestamp):
	# Seperate logs per day
	return "log_" + timestamp.strftime("%Y") + timestamp.strftime("%m") + timestamp.strftime("%d") + ".csv"
	pass

def writeLine(timestamp, line):
	try:
		print("Log: logging...")		

		# Create file / append to end of log file
		filePath = os.path.join(settings.appDir, logPath, currentFilename(timestamp))
		with open(filePath, "a") as f:
			f.write(line + "\n")

		print("Log: line saved to:", filePath)
	except Exception as ex:
		print("Log: Error:", str(ex))
	pass

def listCompletedFiles(timestamp):
	# List files except file currently in use
	dirPath = os.path.join(settings.appDir, logPath)
	currentFile =  currentFilename(timestamp)
	return [os.path.join(dirPath, f) for f in os.listdir(dirPath) if os.path.isfile(os.path.join(dirPath, f)) and f != currentFile]

def readCompletedFiles(timestamp):
	try:
		print("Log: reading logs...")
		data = dict()
		for fp in listCompletedFiles(timestamp):
			with open(fp, "r") as f:
				# Remove 'log_' prefix
				# Originally logs was per month in format yyyyMM, so pad to 8 chars to result in format yyyyMMdd
				date = os.path.basename(fp)[4:-4].ljust(8, '0')
				data[date] = f.read()

			print("Log: Read:", fp)

		if len(data) == 0:
			return None, None
		elif len(data) == 1:
			name, content = list(data.items())[0]
		else:
			# Order data by date
			odata = collections.OrderedDict(sorted(data.items(), key=lambda t: t[0]))
			# Filename is date range
			dates = list(odata.keys())
			name = dates[0] + "_" + dates[-1]
			# Combine content
			content = "".join(odata.values())

		name += ".csv"
		return name, content
	except Exception as ex:
		print("Log: Error:", str(ex))
		return None, None
	pass

def removeCompletedFiles(timestamp):
	try:
		print("Log: removing logs...")
		for fp in listCompletedFiles(timestamp):
			os.remove(fp)
			print("Log: Removed:", fp)
	except Exception as ex:
		print("Log: Error:", str(ex))
	pass

def createTestLogs(timestamp, days):
	checkFolder()

	for d in range(days):
		ts = timestamp - timedelta(days=d)
		writeLine(ts, ts.isoformat() + ",Testing!")

def test():	
	timestamp = datetime.now()
	createTestLogs(timestamp, 7)	
	filename, content = readCompletedFiles(timestamp)
	removeCompletedFiles(timestamp)

if __name__ == '__main__':
	test()

	while True:
		time.sleep(1)
