import time
import subprocess
import binascii
import bluetooth
from bluetooth.ble import DiscoveryService
from bluetooth.ble import BeaconService

bluetoothPrefix = "68696a6f" # Hex for hijo

class NearbyDevice:
	def __init__(self, deviceId, signalStrength, proximity):
		self.DeviceId = deviceId
		self.SignalStrength = signalStrength
		self.Proximity = proximity

class Beacon(object):
	def __init__(self, data, address):
		self._uuid = data[0]
		self._major = data[1]
		self._minor = data[2]
		self._power = data[3]
		self._rssi = data[4]
		self._address = address
		
	def __str__(self):
		ret = "Beacon: address:{ADDR} uuid:{UUID} major:{MAJOR}"\
				" minor:{MINOR} txpower:{POWER} rssi:{RSSI}"\
				.format(ADDR=self._address, UUID=self._uuid, MAJOR=self._major,
						MINOR=self._minor, POWER=self._power, RSSI=self._rssi)
		return ret

def deviceIdToUuid(deviceId):
	x = str(binascii.hexlify(bytes(deviceId[:4], "ascii")),"ascii")
	y = str(binascii.hexlify(bytes(deviceId[5:9], "ascii")),"ascii")
	s = "-"
	return s.join([bluetoothPrefix, "0000", x[:4], x[4:], y + "0000"])

def uuidTodeviceId(uuid):
	x = str(binascii.unhexlify(uuid[14:18] + uuid[19:23]),"ascii")
	y = str(binascii.unhexlify(uuid[24:32]),"ascii")
	s = "-"
	return s.join([x, y])

def startBeacon(deviceId):
	try:
		beaconUuid = deviceIdToUuid(deviceId) #HACK: Encode device id in UUID / GUID
		print("Bluetooth: starting beacon: {}".format(beaconUuid))
		service = BeaconService()
		service.start_advertising(
			beaconUuid,
			1, # Major value, range: 1 to 65535
			1, # Minor value, range: 1 to 65535
			1, # TX Power value, range: -40 to 4
			200) # Interval
		#time.sleep(15)
		#service.stop_advertising()
		print("Bluetooth: beacon advertising!")
	except Exception as ex:
		print("Bluetooth: Error:", str(ex))
	pass

def scanBeacons():
	service = BeaconService()
	devices = service.scan(10) # Timeout
	#print("found %d beacons" % len(devices))

	beacons = []
	for address, data in list(devices.items()):
		beacons.append(Beacon(data, address))		
		#print(b)
		#readLowEnergyDeviceName(address, b._uuid)

	return beacons

def readLowEnergyDeviceName(address, uuid):
	print("Read name:", address, uuid)
	requester = GATTRequester(address, False)
	sys.stdout.flush()
	requester.connect(True)
	data = requester.read_by_uuid(uuid)[0]

	try:
		print("Device name: " + data.decode("utf-8"))
	except AttributeError:
		print("Device name: " + data)
	pass

def scanLowEnergyDevices():
	service = DiscoveryService()
	devices = service.discover(2)
	print("found %d low energy devices" % len(devices))

	for address, name in devices.items():
		print("name: {}, address: {}".format(name, address))

def scanDevices():
	devices = bluetooth.discover_devices(lookup_names=True, flush_cache=True)
	print("found %d devices" % len(devices))

	for addr, name in devices:
		print("name: {}, address: {}".format(name, addr))

def makeDiscoverable(name):
	cmd = "sudo hciconfig hci0 name '" + name + "'"
	subprocess.check_output(cmd, shell = True)

def getNearbyDevices():
	print("Bluetooth: scanning...")
	nearbyDevices = []

	for n in scanBeacons():
		#HACK: All HiJo Devices start with predefined prefix
		if n._uuid.startswith(bluetoothPrefix):
			nearbyDevices.append(NearbyDevice(
				uuidTodeviceId(n._uuid), #HACK: Device id is encoded in UUID / GUID
				n._rssi, ""))

	print("Bluetooth: {} devices found:".format(len(nearbyDevices)))
	for d in nearbyDevices:
		print("Device Id:{0}, Signal Strength:{1}".format(d.DeviceId, d.SignalStrength))

	return nearbyDevices

def test():
	makeDiscoverable("Test")
	scanDevices()
	scanLowEnergyDevices()
	startBeacon("test-0000")
	scanBeacons()