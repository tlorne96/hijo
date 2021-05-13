from datetime import datetime
import time
import os
import os.path
import hashlib
import zipfile

from azure.storage.blob import BlockBlobService, PublicAccess

account_name = "hijoprodausse"
container_name = "firmware"

if os.name == 'nt':
	# Running on Windows
	app_path = "emulator/app"
else:
	app_path = "/home/pi/HiJo/app"

zipSuffix = ".zip"
updateSuffix = ".update"
backupSuffix = ".backup"
version_filename = "version.txt"
hashKey = "hashCheck"

def blobService(key):
	# Creates blob service
	print("Account name:", account_name)
	return BlockBlobService(account_name=account_name, account_key=key)

def toVersionNumber(version):
	# Converts version to int
	return int(version.replace(".",""))
	pass	

def appVersion(path):
	# Retrieves app version from text file
	try:
		if not os.path.exists(path):
			print("App directory does not exist yet.")
			return "0" # If the app directory does not exist download new version
			
		with open(os.path.join(path, version_filename), "r") as f:
			version = f.read()
			print("App version:", version)
			return version
	except Exception as ex:
		print("Failed reading app version", str(ex))
		return "0" # If for some reason the version number cannot be read or parsed, rather override the current version
	pass

def remoteVersion(service):
	# Retrieves remote version from blob
	try:
		blob = service.get_blob_to_text(container_name, version_filename, 'utf-8')
		version = blob.content
		print("Remote version:", version)
		return version
	except Exception as ex:
		print("Failed reading remote version", str(ex))
		return "0" # Do not update if remote version is not available
	pass

def appHash(path):
	# Calculate md5 hash of dir
	m = hashlib.md5()

	for root, dirs, files in os.walk(path):
		for f in files:
			if not f.endswith("pyc"): # Ignore compiled Python
				with open(os.path.join(root, f), 'rb') as file:
					while True:
						# Read file in chunks
						data = file.read(4096)
						if not data:
							break
						else:
							m.update(data)

	hash = m.hexdigest()
	print("App '" + path + "' hash:", hash)
	return hash

def remoteHash(service, version):
	# Get remote app hash from blob metadata
	 metadata = service.get_blob_metadata(container_name, version + zipSuffix)  # metadata={'val1': 'foo', 'val2': 'blah'}
	 hash = metadata[hashKey]
	 print("Remote hash:", hash)
	 return hash

def removeDir(path):
	# Remove sub-files and then dir
	for root, dirs, files in os.walk(path, topdown=False):
		for f in files:
			os.remove(os.path.join(root, f))
		for d in dirs:
			os.rmdir(os.path.join(root, d))

	os.rmdir(path)

def downloadUpdate(service, path, version):
	print("Downloading update...")
	downloadPath = path + zipSuffix

	# Remove previous downloads
	if os.path.exists(downloadPath):
		os.remove(downloadPath)
		
	# Download app
	service.get_blob_to_path(container_name, version + zipSuffix, downloadPath)

	return downloadPath

def extractUpdate(path, downloadPath):
	print("Extracting update...")
	updatePath = path + updateSuffix

	# Remove previous extracts
	if os.path.exists(updatePath):
		removeDir(updatePath)
		
	# Extract files
	with zipfile.ZipFile(downloadPath, 'r') as zip:
		zip.extractall(updatePath)

	return updatePath

def verifyUpdate(path, hash):
	print("Verifying update...")

	if os.path.exists(path):
		# Ensure hash match downloaded version
		if hash == appHash(path):
			return True
		else:
			print("Verification failed: hash does not match.")
			return False
	else:
		print("Verification failed: folder missing.")
		return False

def applyUpdate(newPath):
	print("Applying update...")	
	backupPath = app_path + backupSuffix

	# Remove previous backup
	if os.path.exists(backupPath):
		removeDir(backupPath)

	# Swap current version to backup if available
	if os.path.exists(app_path):
		os.rename(app_path, backupPath)
	
	# Swap new version to current
	os.rename(newPath, app_path)

if __name__ == '__main__':
	try:
		print("Checking for HiJo updates...")
		service = blobService("")

		# Update if new version is available
		version = remoteVersion(service)
		if toVersionNumber(version) > toVersionNumber(appVersion(app_path)):
			print("Updating app...")
			
			# Get update app hash for validation
			hash = remoteHash(service, version)

			# Download update
			downloadPath = downloadUpdate(service, app_path, version)

			# Verify update
			if verifyUpdate(downloadPath, hash):
				# Extract update
				updatePath = extractUpdate(app_path, downloadPath)

				# Apply update
				applyUpdate(updatePath)

				# Chech new version
				appVersion(app_path)
				print("HiJo has successfully been updated.")
		else:
			print("HiJo is running the latest version.")
	except Exception as ex:
		print("Error updating HiJo:", str(ex))
	pass