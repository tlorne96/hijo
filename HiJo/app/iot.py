from datetime import datetime
import time
#import threading
#import functools
from iothub_client import IoTHubClient, IoTHubTransportProvider, IoTHubMessage

import setup
import bluetoothHelper
import log

iot_PROTOCOL = IoTHubTransportProvider.MQTT
iot_CONNECTION_STRING = "HostName=%s;DeviceId=%s;SharedAccessKey=%s"
iot_CALLBACK_TIMEOUT = 15

iot_STARTUP_JSON = "{\"deviceId\":\"%s\",\"devicetime\":\"%s\",\"deviceName\":\"%s\",\"type\":\"Startup\"}"
iot_DATA_JSON = "{\"deviceId\":\"%s\",\"devicetime\":\"%s\",\"deviceName\":\"%s\",\"type\":\"Telemetry\",\"temp\":%.2f,\"light\":%.2f,\"height\":%.2f,\"gyroX\":%.3f,\"gyroY\":%.3f,\"gyroZ\":%.3f,\"gyroMovement\":\"%s\",\"buttonId\":%d,\"buttonLabel\":\"%s\",\"nearby\":[%s]}"
iot_NEARBY_JSON = "{\"deviceId\":\"%s\",\"signalStrength\":%.4f,\"proximity\":\"%s\"}"
iot_ALERT_JSON = "{\"deviceId\":\"%s\",\"devicetime\":\"%s\",\"deviceName\":\"%s\",\"type\":\"Alert\",\"buttonId\":%d,\"buttonLabel\":\"%s\"}"

iot_returned = False
iot_result = True
iot_message = ""
iot_logUploadTimestamp = None

def iotInit():
	# Initialize IoT Hub client
	iot_connectionString = iot_CONNECTION_STRING % (setup.iotHost, setup.iotDeviceId, setup.iotDeviceAccessKey)
	iotClient = IoTHubClient(iot_connectionString, iot_PROTOCOL)
	return iotClient

def iotSendStartup(iotClient, deviceId, deviceTime, deviceName):
	print("IoT: sending startup message...")

	# Construct JSON message
	msg = iot_STARTUP_JSON % (deviceId, deviceTime.isoformat(), deviceName) 
	
	# Send to IoT sync to catch error
	return iotSendSync(iotClient, msg, False)

def iotSendTelemetry(iotClient, deviceId, deviceTime, deviceName, temp, light, height, gyroX, gyroY, gyroZ, gyroMovement,
					 buttonId, buttonLabel, nearbyDevices):
	print("IoT: sending telemetry...")
	
	# Construct JSON message
	nearby = []
	for n in nearbyDevices:
		nearby.append(iot_NEARBY_JSON % (n.DeviceId, n.SignalStrength, n.Proximity))

	s = "," 
	nearbyCollection = s.join(nearby)
	msg = iot_DATA_JSON % (deviceId, deviceTime.isoformat(), deviceName, 
						   temp, light, height, gyroX, gyroY, gyroZ, gyroMovement, buttonId, buttonLabel, nearbyCollection) 

	# Send to IoT sync to catch error
	return iotSendSync(iotClient, msg, False)

def iotSendAlert(iotClient, deviceId, deviceTime, deviceName, buttonId, buttonLabel):
	print("IoT: sending alert...")
	
	# Construct JSON message
	msg = iot_ALERT_JSON % (deviceId, deviceTime.isoformat(), deviceName, buttonId, buttonLabel) 

	# Send to IoT async
	return iotSendAsync(iotClient, msg, True)

def iotSendSync(iotClient, msg, alert):
	global iot_returned
	global iot_result
	global iot_message

	try:
		# Send aync
		iot_returned = False
		iot_result, iot_message = iotSendAsync(iotClient, msg, alert, False)

		if iot_result:
			# Await result
			timeout = time.time() + iot_CALLBACK_TIMEOUT
			while not iot_returned:
				if time.time() > timeout:
					return False, "Confirmation timed out"

				time.sleep(0.5)

		return iot_result, iot_message
	except Exception as ex:
		error = str(ex)
		print("IoT: Error:", error)
		return False, error
	pass

def send_confirmation_callback(message, result, user_context):
	global iot_returned
	global iot_result
	global iot_message

	try:
		print("IoT: message confirmation = %s" % (result))
		iot_result = str(result) == "OK"
		iot_message = str(result) #message
		iot_returned = True
	except Exception as ex:
		print("IoT: Error:", str(ex))
	pass

def iotSendAsync(iotClient, msg, alert, async = True):
	try:
		# Encode message 
		message = IoTHubMessage(bytearray(msg, 'utf8'))
		   
		# Add message properties
		prop_map = message.properties()
		if alert:
			prop_map.add("alert", "true")
		else:
			prop_map.add("alert", "false")

		# Send message
		if async:
			iotClient.send_event_async(message, send_confirmation_callback_async, None)
		else:
			iotClient.send_event_async(message, send_confirmation_callback, None)

		return True, ""
	except Exception as ex:
		error = str(ex)
		print("IoT: Error:", error)
		return False, error
	pass

def send_confirmation_callback_async(message, result, user_context):
	try:
		print("IoT: async message confirmation = %s" % (result))
	except Exception as ex:
		print("IoT: Error:", str(ex))
	pass

def iotUploadLogs(iotClient, timestamp):
	global iot_logUploadTimestamp

	try:
		iot_logUploadTimestamp = timestamp
		filename, content = log.readCompletedFiles(iot_logUploadTimestamp)
		if filename:
			iotClient.upload_blob_async(filename, content, len(content), blob_upload_conf_callback, 0)
			print("IoT: Uploading log:", filename)
	except Exception as ex:
		print("IoT: Error:", str(ex))
	pass

def blob_upload_conf_callback(result, user_context):
	global iot_logUploadTimestamp

	try:
		print("IoT: file upload confirmation = %s" % (result))
		if iot_logUploadTimestamp:
			log.removeCompletedFiles(iot_logUploadTimestamp)

		iot_logUploadTimestamp = None
	except Exception as ex:
		print("IoT: Error:", str(ex))
	pass

def test():
	timestamp  = datetime.now()
	iotClient = iotInit()
	iotSendStartup(iotClient, "test", timestamp, "Test Device")
	iotSendTelemetry(iotClient, "test", timestamp, "Test Device", 0, 0, 0, 0, 0, 0, "", 0, "", [])
	iotSendAlert(iotClient, "test", timestamp, "Test Device", 0, "")
	log.createTestLogs(timestamp, 7)
	iotUploadLogs(iotClient, timestamp)

if __name__ == '__main__':
	test()

	while True:
		time.sleep(1)