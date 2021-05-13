import time
import math
import RPi.GPIO as GPIO

height_GPIO_TRIG = 20
height_GPIO_ECHO = 26
height_MAX_TIME = 0.04 # Seconds
height_pulse_factor = 18082 # 17150

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(height_GPIO_TRIG, GPIO.OUT)
GPIO.setup(height_GPIO_ECHO, GPIO.IN)

def getHeight():
	try:
		print("Height sensor: measuring...")
		GPIO.output(height_GPIO_TRIG, True)
		time.sleep(0.00001)
		GPIO.output(height_GPIO_TRIG, False)

		# Ensure start time is set in case of very quick return
		start = time.time()

		timeout = time.time() + height_MAX_TIME
		while GPIO.input(height_GPIO_ECHO) == 0:
			if time.time() > timeout:
				raise Exception("Sensor timed out")

			start = time.time()

		# Ensure stop time is set in case of very quick return
		stop = time.time()

		# Wait for end of echo response
		timeout = time.time() + height_MAX_TIME
		while GPIO.input(height_GPIO_ECHO) == 1:
			if time.time() > timeout:
				raise Exception("Sensor timed out")

			stop = time.time()

		# Determine height from pulse duration
		pulse_duration = stop - start
		distance = pulse_duration * height_pulse_factor / 100
		distance = round(distance, 2)
		print("Height sensor: measurement:", distance, "m", pulse_duration)
		return distance
	except Exception as ex:
		print("Height sensor: Error:", str(ex))
		return 0
	pass

def test():
	getHeight()

#if __name__ == '__main__':
#	while True:
#		getHeight()
#		time.sleep(0.5)