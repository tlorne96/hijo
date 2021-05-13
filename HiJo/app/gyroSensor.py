import time
from multiprocessing import Process, Lock, Value
from mpu6050 import mpu6050

gravity = 9.80665

try:
	gyroSensor = mpu6050(0x68)
except:
	gyroSensor = None
	pass

def getMovement():
	try:
		if not gyroSensor:
			raise Exception("Sensor not connected")
			pass
		else:
			#print("Gyro sensor: measuring...")
			values = gyroSensor.get_accel_data()
			movement = "" #TODO
			#print("Gyro sensor: acceleration: x={0:0.3f} m/s^2 y={1:0.3f} m/s^2 z={2:0.3f} m/s^2".format(x, y, z))
			#orientation = gyroSensor.orientation
			#print("Gyro sensor: orientation: {0}".format(orientation))
			return values["x"], values["y"], values["z"], movement
	except Exception as ex:
		print("Gyro sensor: Error:", str(ex))
		return 0, 0, gravity, ""
	pass

def gyroLoop(l, x, y, z, t):
	try:
		if not gyroSensor:
			raise Exception("Sensor not connected")
			pass
		else:
			while True:
				l.acquire()
				try:
					xTemp, yTemp, zTemp, movementTemp = getMovement()
					tTemp = abs(xTemp) + abs(yTemp) + abs(zTemp - gravity)

					if tTemp > t.value:
						x.value = xTemp
						y.value = yTemp
						z.value = zTemp
						t.value = tTemp
				finally:
					l.release()

				time.sleep(0.1)
	except Exception as ex:
		print("Gyro sensor: Error:", str(ex))
	pass

def test():
	getMovement()