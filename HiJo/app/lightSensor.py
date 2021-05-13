import time
import smbus

def getLight():
	try:
		print("Light sensor: measuring...")
		bus = smbus.SMBus(1)
		bus.write_byte_data(0x39, 0x00 | 0x80, 0x03)
		bus.write_byte_data(0x39, 0x01 | 0x80, 0x02)
		#time.sleep(0.5)

		print("Light sensor: reading bus")
		data = bus.read_i2c_block_data(0x39, 0x0C | 0x80, 2)
		data1 = bus.read_i2c_block_data(0x39, 0x0E | 0x80, 2)
		ch0 = data[1]*256 + data[0]
		ch1 = data1[1]*256 + data1[0]
		light = ch0 - ch1

		print("Light sensor: measurement:", light)
		return light
	except Exception as ex:
		print("Light sensor: Error:", str(ex))
		return 0
	pass

def test():
	getLight()