from datetime import datetime
import time
import os
import os.path
import subprocess
import configparser

import settings
import lcdDisplay

# App
appVersion = ""

# Environment
wifiName = ""
wifiPwd = ""
wifiCountryCode = ""

# Added 13/11/2018
wifiKeyMgmt = ""
wifiEap = ""
wifiIdentity = ""

iotHost = ""
tempUoM = ""
heightUoM = ""
timeZone = ""

# Device
deviceName = "" # Freidly name to identify device
iotDeviceId = ""
iotDeviceAccessKey = ""

def readAppVersion():
	global appVersion

	with open(os.path.join(settings.appDir, settings.versionFilename), "r") as f:
		appVersion = f.read()
		print("App version:", appVersion)

	pass

def getUsbName():
	cmd = "ls " + settings.usbDir
	proc = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid,stdout=subprocess.PIPE)
	line = proc.stdout.readline()

	if line:
		usbName = line.decode("utf-8").rstrip()
	else:
		usbName = None

	return usbName

def readEnvironmentConfig(configPath):
	global wifiName
	global wifiPwd
	global wifiCountryCode
	global wifiKeyMgmt
	global wifiEap
	global wifiIdentity
	global iotHost
	global tempUoM
	global heightUoM
	global timeZone
	
	config = configparser.ConfigParser()
	config.read(configPath)

	wifiName = config[settings.configSection]["wifiName"]
	wifiPwd = config[settings.configSection]["wifiPwd"]
	wifiCountryCode = config[settings.configSection]["wifiCountryCode"]

	if config.has_option(settings.configSection, "wifiKeyMgmt"):
		wifiKeyMgmt = config[settings.configSection]["wifiKeyMgmt"]

	if config.has_option(settings.configSection, "wifiKeyMgmt"):
		wifiEap = config[settings.configSection]["wifiEap"]

	if config.has_option(settings.configSection, "wifiKeyMgmt"):
		wifiIdentity = config[settings.configSection]["wifiIdentity"]
	
	iotHost = config[settings.configSection]["iotHost"]
	tempUoM = config[settings.configSection]["tempUoM"]
	heightUoM = config[settings.configSection]["heightUoM"]

	if config.has_option(settings.configSection, "timeZone"):
		timeZone = config[settings.configSection]["timeZone"]

	pass

def updateEnvironment(configPath):
	print("Setup: updating environment config...")
	lcdDisplay.show("Updating", "Environment...")
	readEnvironmentConfig(configPath)

	# Update local config
	config = configparser.ConfigParser()	
	config[settings.configSection] = {}

	config[settings.configSection]["wifiName"] = wifiName
	config[settings.configSection]["wifiPwd"] = wifiPwd
	config[settings.configSection]["wifiCountryCode"] = wifiCountryCode

	config[settings.configSection]["wifiKeyMgmt"] = wifiKeyMgmt
	config[settings.configSection]["wifiEap"] = wifiEap
	config[settings.configSection]["wifiIdentity"] = wifiIdentity

	config[settings.configSection]["iotHost"] = iotHost
	config[settings.configSection]["tempUoM"] = tempUoM
	config[settings.configSection]["heightUoM"] = heightUoM

	config[settings.configSection]["timeZone"] = timeZone

	with open(os.path.join(settings.appDir, settings.environmentConfigFile), "w") as configFile:
		config.write(configFile)

	# Update time zone
	if timeZone != "":
		cmd = "sudo timedatectl set-timezone '" + timeZone + "'"
		subprocess.check_output(cmd, shell = True)

	print("Setup: environment updated")

def readDeviceConfig(configPath):
	global deviceName
	global iotDeviceId
	global iotDeviceAccessKey

	config = configparser.ConfigParser()
	config.read(configPath)
	deviceName = config[settings.configSection]["deviceName"]
	iotDeviceId = config[settings.configSection]["iotDeviceId"]
	iotDeviceAccessKey = config[settings.configSection]["iotDeviceAccessKey"]

def updateDevice(configPath):
	print("Setup: Updating device config...")
	lcdDisplay.show("Updating", "Device...")
	readDeviceConfig(configPath)

	# Update local config
	config = configparser.ConfigParser()	
	config[settings.configSection] = {}
	config[settings.configSection]["deviceName"] = deviceName
	config[settings.configSection]["iotDeviceId"] = iotDeviceId
	config[settings.configSection]["iotDeviceAccessKey"] = iotDeviceAccessKey

	with open(os.path.join(settings.appDir, settings.deviceConfigFile), "w") as configFile:
		config.write(configFile)

	print("Setup: device updated")

def updateWiFi():
	# Configure WiFi
	#cmd = "sudo su wpa_passphrase " + wifiName + " " + wifiPwd + " >> /etc/wpa_supplicant/wpa_supplicant.conf"
	#proc = subprocess.Popen(cmd, shell=True) #, preexec_fn=os.setsid,stdout=subprocess.PIPE)
	#line = proc.stdout.readline()

	wifiConfig = []
	wifiConfig.append("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
	wifiConfig.append("update_config=1\n")

	if wifiCountryCode != "":
		wifiConfig.append("country=" + wifiCountryCode + "\n")

	wifiConfig.append("network={\n")
	wifiConfig.append("ssid=\"" + wifiName + "\"\n")

	if wifiKeyMgmt == "":
		if wifiPwd != "":
			wifiConfig.append("psk=\"" + wifiPwd + "\"\n")
		else:
			wifiConfig.append("key_mgmt=NONE\n")
	else:
		wifiConfig.append("key_mgmt=" + wifiKeyMgmt + "\n")

		if wifiKeyMgmt == "WPA-PSK":
			wifiConfig.append("psk=\"" + wifiPwd + "\"\n")
		
	if wifiEap != "":
		wifiConfig.append("eap=" + wifiEap + "\n")
		wifiConfig.append("identity=\"" + wifiIdentity + "\"\n")

		if wifiEap == "TLS":
			wifiConfig.append("ca_cert=\"/etc/cert/ca.pem\"\n")
			wifiConfig.append("client_cert=\"/etc/cert/user.pem\"\n")
			wifiConfig.append("private_key=\"/etc/cert/user.prv\"\n")
			wifiConfig.append("private_key_passwd=\"" + wifiPwd + "\"\n")
		elif wifiEap == "PEAP":
			wifiConfig.append("password=\"" + wifiPwd + "\"\n")
			wifiConfig.append("ca_cert=\"/etc/cert/ca.pem\"\n")
			wifiConfig.append("phase1=\"peaplabel=0\"\n")
			wifiConfig.append("phase2=\"auth=MSCHAPV2\"\n")
		elif wifiEap == "TTLS":
			wifiConfig.append("password=\"" + wifiPwd + "\"\n")
			wifiConfig.append("ca_cert=\"/etc/cert/ca.pem\"\n")
			wifiConfig.append("phase2=\"auth=MD5\"\n")
			
	wifiConfig.append("}\n")

	with open('/etc/wpa_supplicant/wpa_supplicant.conf','w') as f:
		f.writelines(wifiConfig)

	# Reconfigure WiFi
	cmd = "wpa_cli -i wlan0 reconfigure"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,) #, preexec_fn=os.setsid)
	line = proc.stdout.readline()

	# Allow connection to stabilize
	time.sleep(5)
		
	# Test internet connection
	#if commandExists("dhclient"):
	#	os.popen("dhclient " + winame)
	#elif commandExists("dhcpcd"):
	#	os.popen("dhcpcd " + winame).read()
	#else:
	#	raise Exception("Require command 'dhclient'/'dhcpcd'")
		
	#ontest = os.popen("ping -c 1 google.com").read()
	#if ontest == '':
	#	raise Exception("No internet connection")

	pass

def updateConfig():
	try:
		print("Setup: checking for config updates...")
		update = False

		readAppVersion()

		# Check if USB is connected and find name
		usb = getUsbName()
		if usb:
			print("Setup: USB connected:", usb)

			# Check if the USB contain environment config file
			configPath = os.path.join(settings.usbDir, usb, settings.environmentConfigFile)
			if os.path.isfile(configPath):
				updateEnvironment(configPath)
				update = True

				# Check if cert folder is available
				certPath = os.path.join(settings.usbDir, usb, "cert")
				if os.path.isdir(certPath):
					if not os.path.isdir("/etc/cert"):
						cmd = "sudo mkdir /etc/cert"
						subprocess.check_output(cmd, shell = True)

					cmd = "sudo cp -rf " + certPath + "/* /etc/cert"
					subprocess.check_output(cmd, shell = True)

			# Check if the USB contain device config file
			configPath = os.path.join(settings.usbDir, usb, settings.deviceConfigFile)
			if os.path.isfile(configPath):
				if update:
					time.sleep(3) # Wait before updating display

				updateDevice(configPath)

		# Always read config from local files
		print("Setup: reading local config")
		configPath = os.path.join(settings.appDir, settings.environmentConfigFile)
		if os.path.isfile(configPath):
			readEnvironmentConfig(configPath)
		else:
			return False

		configPath = os.path.join(settings.appDir, settings.deviceConfigFile)
		if os.path.isfile(configPath):
			readDeviceConfig(configPath)
		else:
			return False

		if update:
			print("Setup: update WiFi...")
			updateWiFi()

		return True
	except Exception as ex:
		print("Status: Error:", str(ex))
		return False
	pass

def test():
	updateConfig()
	pass