import time
#import board
#from adafruit_blinka import digitalIO
#from adafruit_ds18x20 import DS18X20
#from ds18b20 import DS18B20

import os 
import glob

temp_MAX_TIME = 0.5 # Seconds

try:
	os.system('modprobe w1-gpio')
	os.system('modprobe w1-therm')
	temp_base_dir = '/sys/bus/w1/devices/'
	temp_folder = glob.glob(temp_base_dir + '28*')[0]
	temp_file = temp_folder + '/w1_slave'
except:
	temp_file = None
	pass

def read_temp_raw():
	if not temp_file:
		raise Exception("Sensor not connected")
		pass

	f = open(temp_file, 'r')
	lines = f.readlines()
	f.close()
	return lines

def read_temp(): 
	lines = read_temp_raw()

	timeout = time.time() + temp_MAX_TIME
	while lines[0].strip()[-3:] != 'YES':
		if time.time() > timeout:
			raise Exception("Sensor timed out")

		time.sleep(0.2)		
		lines = read_temp_raw()
		
	equals_pos = lines[1].find('t=')  
	if equals_pos != -1:		
		temp_string = lines[1][equals_pos + 2:]		
		temp_c = float(temp_string) / 1000.0		
		#temp_f = temp_c * 9.0 / 5.0 + 32.0		
		return temp_c
	else:
		raise Exception("No reading")

def getTemp():
	try:
		print("Temp sensor: measuring...")
	
		# Initialize one-wire bus on board pin D5.
		#ow_bus = OneWireBus(board.D5)

		# Scan for sensors and grab the first one found.
		#ds18 = DS18X20(ow_bus, ow_bus.scan()[0])

		#sensor = DS18B20()
	
		# Take 5 measurements
		values = []
		for x in range(4): 
			#values.append(ds18.temperature())	  
			#values.append(sensor.get_temperature()) 
			values.append(read_temp()) 
			time.sleep(0.5)

		# Use the average temp
		temp = sum(values) / float(len(values))
		print("Temp sensor: measurement: {0:0.3f}C".format(temp))
		return temp
	except Exception as ex:
		print("Temp sensor: Error:", str(ex))
		return 0
	pass

def test():
	getTemp()
