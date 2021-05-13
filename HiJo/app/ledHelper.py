import RPi.GPIO as IO
import time

led = 21
IO.setwarnings(False)

IO.setmode(IO.BCM)
IO.setup(led, IO.OUT)

def lightOn():
	try:
		IO.output(led, IO.HIGH)
	except Exception as ex:
		print("LED: Error:", str(ex))
	pass

def lightOff():
	try:
		IO.output(led, IO.LOW)
	except Exception as ex:
		print("LED: Error:", str(ex))
	pass

def test():
	lightOn()
	lightOff()
