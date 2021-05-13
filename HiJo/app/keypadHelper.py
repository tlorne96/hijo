import time
from datetime import datetime
from multiprocessing import Process, Lock, Value

import RPi.GPIO as GPIO
import rpi_gpio

import ledHelper
import lcdDisplay
import setup
import iot

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

keypad_ROW_PINS = [16,14,15,17]
keypad_COL_PINS = [5,6,13]

#keypadIds = [
#	[1,2,3],
#	[4,5,6],
#	[7,8,9],
#	[10,11,12]
#]

#keypadNames = [
#	"Happy",
#	"Anxious",
#	"Bored",
#	"Sad",
#	"Relaxed",
#	"Interested",
#	"Teacher",
#	"Confirm",
#	"Cancel"
#]

#keyScreenDisplay = [
#	"Happy :)",
#	"I feel anxious",
#	"I am bored", 
#	"I'm a bit sad", 
#	"Relaxed & calm",
#	"I'm interested",
#	"Help me teacher!"  
#]

keypadIds = [
	[3,2,1],
	[6,5,4],
	[9,11,7],
	[10,8,12]
]

keypadNames = [
	"Happy",
	"Anxious",
	"Relaxed",
	"Sad",
	"Bored",
	"Interested",
	"Teacher",
	"Confirm",
	"Cancel"
]

keyScreenDisplay = [
	"Happy :)",
	"I feel anxious",
	"Relaxed & calm",
	"I'm a bit sad", 
	"I am bored", 
	"I'm interested",
	"Help me teacher!"  
]

iotClient = None
keypadLock = None
tempKeyId = None
currentKeyId = None
teacherAssist = None
sharedHeight = None
sharedTemp = None

def registerKeypad(lock, tempId, currentId, teacherAssistFlag, height, temp):
	try:
		global iotClient
		global keypadLock
		global tempKeyId
		global currentKeyId
		global teacherAssist
		global sharedHeight
		global sharedTemp

		iotClient = iot.iotInit()
		keypadLock = lock
		tempKeyId = tempId
		currentKeyId = currentId
		teacherAssist = teacherAssistFlag
		sharedHeight = height
		sharedTemp = temp

		factory = rpi_gpio.KeypadFactory()
		keypad = factory.create_keypad(keypad=keypadIds, row_pins=keypad_ROW_PINS, col_pins=keypad_COL_PINS)
		keypad.registerKeyPressHandler(handleKeyPress)
		print("Keypad: listening...")
	except Exception as ex:
		print("Keypad: Error:", str(ex))
	pass

def handleKeyPress(key):
	global keypadLock
	global tempKeyId
	global currentKeyId
	global teacherAssist

	if keypadLock:
		keypadLock.acquire()
		try:
			if key <= 9:
				print("Keypad: id:", key, "name:", getKeyName(key))

				if key == 8: # Confirm
					if tempKeyId.value > 0:
						# Submit values
						currentKeyId.value = tempKeyId.value

						# Handle teacher assist
						if (tempKeyId.value == 7):
							if not teacherAssist.value:
								# Start teacher assist
								teacherAssist.value = True
								ledHelper.lightOn()
								iot.iotSendAlert(iotClient, setup.iotDeviceId, datetime.now(), setup.deviceName,
												tempKeyId.value, getKeyName(tempKeyId.value))

								# Set display message	
								lcdDisplay.show("Waiting for", "teacher...")
							else:
								# Stop teacher assist
								teacherAssist.value = False
								ledHelper.lightOff()
								resetDisplay(tempKeyId, teacherAssist)
						else:
							# Set display message		
							lcdDisplay.show("Thank you for", "letting me know")

							# Wait before updating display
							time.sleep(3)
							resetDisplay(tempKeyId, teacherAssist)
					else:
						print("Keypad: Confirm") # Not used atm
				elif key == 9: # Cancel
					if teacherAssist.value:
						# Stop teacher assist
						teacherAssist.value = False
						ledHelper.lightOff()

					resetDisplay(tempKeyId, teacherAssist)
				else:
					if tempKeyId.value == 7 and teacherAssist.value:
						# Stop teacher assist
						teacherAssist.value = False
						ledHelper.lightOff()
						resetDisplay(tempKeyId, teacherAssist)
					elif tempKeyId.value > 0 or teacherAssist.value:
						print("Keypad: Awaiting input")
					else:
						# Set temp value and display message
						tempKeyId.value = key
						lcdDisplay.show(keyScreenDisplay[tempKeyId.value - 1], "Confirm / Cancel")
						Process(target=awaitConfirmCancel).start()
			else:
				print("Keypad: id:", key, "name:", "Not used")
		except Exception as ex:
			print("Keypad: Error:", str(ex))
		finally:
			keypadLock.release()
	pass

def awaitConfirmCancel():
	global keypadLock
	global tempKeyId
	global teacherAssist

	# Wait before updating display
	time.sleep(10)

	keypadLock.acquire()
	try:		
		resetDisplay(tempKeyId, teacherAssist)
	finally:
		keypadLock.release()
	pass

def resetDisplay(tempKeyId, teacherAssist):
	# Teacher assist should persist until manually cancelled
	if not teacherAssist.value:
		tempKeyId.value = 0
		lcdDisplay.showDefault(sharedHeight.value, sharedTemp.value, setup.heightUoM, setup.tempUoM)
	pass

def getKeyName(id):
	if id > 0:
		return keypadNames[id - 1]
	else:
		return ""

def test():
	keypadLock = Lock()
	keypadTempKeyId = Value('i', 0)
	keypadCurrentKeyId = Value('i', 0)
	teacherAssistFlag = Value('b', False)
	height = Value('d', 0.0)
	temp = Value('d', 0.0)
	registerKeypad(keypadLock, keypadTempKeyId, keypadCurrentKeyId, teacherAssistFlag, height, temp)
	getKeyName(1)