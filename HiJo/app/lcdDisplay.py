import time
import Adafruit_CharLCD as LCD

try:
	lcd_characters = 16
	lcd_rs		= 27
	lcd_en		= 22
	lcd_d4		= 25
	lcd_d5		= 24
	lcd_d6		= 23
	lcd_d7		= 18
	lcd_backlight = 4
	lcd_columns = 16
	lcd_rows = 2
	lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, 
							   lcd_columns, lcd_rows, lcd_backlight)
except:
	lcd = None
	pass

def showDefault(height, temp, heightUoM, tempUoM):
	# Display Height
	if heightUoM == "ft":
		displayHeight = "%.1fft" % (height * 3.28084)
	else:
		displayHeight = "%.1fm" % (height)

	# Display Temp
	if tempUoM == "F":
		displayTemp = "%.0fF" % ((temp * 9/5) + 32)
	else:
		displayTemp = "%.0fC" % (temp)

	# Update display
	defaultSecondLine = displayHeight.ljust(8) + displayTemp.rjust(8)

	show("How are you?", defaultSecondLine)

def show(line1, line2):
	try:
		if not lcd:
			raise Exception("Sensor not connected")
			pass

		lcd.clear()
		lcd.message(line1 + "\n" + line2)
	except Exception as ex:
		print("LCD: Error:", str(ex))
	pass

def test():
	show("Hello", "World")