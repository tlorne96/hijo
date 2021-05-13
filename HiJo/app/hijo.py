import time
from datetime import datetime
from multiprocessing import Process, Lock, Value

import lcdDisplay
import setup

executionDelay = 60
cinfigLoaded = False

def load():	
	global configLoaded

	print("Starting up...")
	lcdDisplay.show("Hello", "Getting ready...")
	time.sleep(3) # Wait before updating display
	configLoaded = setup.updateConfig()

load()

import keypadHelper
import tempSensor
import lightSensor
import heightSensor
import gyroSensor
import bluetoothHelper
import log
import iot

def measurementLoop(keypadLock, keypadTempKeyId, keypadCurrentKeyId, keypadTeacherAssist, sharedHeight, sharedTemp, gyroLock, gyroX, gyroY, gyroZ, gyroT):	
	deviceId = setup.iotDeviceId
	deviceName = setup.deviceName
	print("Running measurement loop for device '{}'...".format(deviceId))	
	timestamp = datetime.now()

	# Test IoT connection and send startup message
	print("IoT: testing connection...")		
	iotClient = iot.iotInit()
	connected, connectionError = iot.iotSendStartup(iotClient, deviceId, timestamp, deviceName)
	if connected:
		lcdDisplay.show("Connected", "to the Hub!")
	else:
		lcdDisplay.show("Not connected", "to the Hub!")
	
	# Log startup locally
	log.checkFolder()	
	csv = "," # CSV format
	csv = csv.join([deviceId, timestamp.isoformat(), deviceName, "Startup",
					str(connected), connectionError])	
	log.writeLine(timestamp, csv)

	# Upload completed (not todays) logs
	iot.iotUploadLogs(iotClient, timestamp)

	# Update Display
	time.sleep(3) # Wait before updating display
	lcdDisplay.show("How are you", "today?")

	while True:
		start = time.time()

		try:			
			timestamp = datetime.now()

			# Read sensors
			temp = tempSensor.getTemp()
			height = heightSensor.getHeight()
			nearbyDevices = bluetoothHelper.getNearbyDevices()

			# Grab gyro values and reset while locked
			gyroLock.acquire()
			try:
				print("Gyro sensor: measuring...")
				gyroXmax = gyroX.value
				gyroYmax = gyroY.value
				gyroZmax = gyroZ.value
				print("Gyro sensor: acceleration: x={0:0.3f} m/s^2 y={1:0.3f} m/s^2 z={2:0.3f} m/s^2".format(gyroXmax, gyroYmax, gyroZmax))
				gyroX.value = 0.0
				gyroY.value = 0.0
				gyroZ.value = 0.0
				gyroT.value = 0.0

				# Light sensor share pin with gyro, read while gyro gyroLock is aquired
				light = lightSensor.getLight()
			finally:
				gyroLock.release()

			# Calculate gyro movement
			gyroMovement = "" #TODO

			# Get key press and clear
			keypadLock.acquire()
			try:
				buttonId = keypadCurrentKeyId.value
				buttonLabel = keypadHelper.getKeyName(buttonId)
				keypadCurrentKeyId.value = 0

				sharedHeight.value = height
				sharedTemp.value = temp

				# Only update display if not awaiting input
				if keypadTempKeyId.value == 0: 
					lcdDisplay.showDefault(height, temp, setup.heightUoM, setup.tempUoM)				   
			finally:
				keypadLock.release()

			# Send message to IoT Hub
			iotSent, iotError = iot.iotSendTelemetry(iotClient, deviceId, timestamp, deviceName, temp, light, height,
										gyroXmax, gyroYmax, gyroZmax, gyroMovement,
										buttonId, buttonLabel, nearbyDevices)   

			# Log telemetry locally
			nearby = []
			for n in nearbyDevices:
				nearby.append(n.DeviceId)
				nearby.append(str(n.SignalStrength))
				nearby.append(n.Proximity)

			ssv = " "
			nearbyCollection = ssv.join(nearby)

			csv = "," # CSV format
			csv = csv.join([deviceId, timestamp.isoformat(), deviceName, "Telemetry", 
							str(temp), str(light), str(height), str(gyroXmax), str(gyroYmax), str(gyroZmax), gyroMovement,
							str(buttonId), buttonLabel, nearbyCollection,
							str(iotSent), iotError])
			log.writeLine(timestamp, csv)

			duration = datetime.now() - timestamp
			print("Successfully ran for: " + str(duration))
		except Exception as ex:
			print("Error:", str(ex))
		finally:
			# Delay
			executionTime = time.time() - start

			if executionTime < executionDelay:
				time.sleep(executionDelay - executionTime)

	print("Exiting...")

if __name__ == '__main__':
	if not configLoaded:
		# Cannot start without configuration files
		lcdDisplay.show("Configuration", "missing")
	else:
		deviceId = setup.iotDeviceId
		version = setup.appVersion
		print("Running device '{}'...".format(deviceId))	
		lcdDisplay.show(deviceId, "ver:" + version)
		time.sleep(5)

		# Start keypad monitoring
		keypadLock = Lock()
		keypadTempKeyId = Value('i', 0)
		keypadCurrentKeyId = Value('i', 0)
		keypadTeacherAssist = Value('b', False)
		sharedHeight = Value('d', 0.0)
		sharedTemp = Value('d', 0.0)
		keypadHelper.registerKeypad(keypadLock, keypadTempKeyId, keypadCurrentKeyId, keypadTeacherAssist, sharedHeight, sharedTemp)
	
		# Start bluetooth broadcasting
		#bluetoothHelper.makeDiscoverable(deviceId)
		bluetoothHelper.startBeacon(deviceId)
		#nearbyDevices = bluetoothHelper.getNearbyDevices()

		# Start measuring gyro in fast loop and use max value intermittently
		gyroLock = Lock()
		gyroX = Value('d', 0.0)
		gyroY = Value('d', 0.0)
		gyroZ = Value('d', 0.0)
		gyroT = Value('d', 0.0)
		Process(target=gyroSensor.gyroLoop, args=(gyroLock, gyroX, gyroY, gyroZ, gyroT)).start()

		# Allow connection and sensors to stabilize
		time.sleep(15)

		# Start measurement loop on seperate thread 
		Process(target=measurementLoop, args=(keypadLock, keypadTempKeyId, keypadCurrentKeyId, keypadTeacherAssist,
										   sharedHeight, sharedTemp, gyroLock, gyroX, gyroY, gyroZ, gyroT)).start()