# Lab 6: Checkpoint 1&2&3
# Group 9: Zhifu Xiao (zx2201), Chen Zhao(cz2498), Chuhan Li(cl3619)

# import modules
import machine
import ssd1306
import time
import ustruct
import network
import json
import ubinascii
import urequests

# set up pins
i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))
oled = ssd1306.SSD1306_I2C(128, 32, i2c)
spi = machine.SPI(1, baudrate=500000, polarity=1, phase=1)
spi.init()
cs = machine.Pin(16, machine.Pin.OUT)
cs.value(0)
message1 = ''
message2 = ''
message3 = ''
prediction = ''

sta_if = network.WLAN(network.STA_IF)
#sta_if.connect('Columbia University', '')
sta_if.connect('Zhifu\'s TC', 'b1ebb640e04e')
sta_if.isconnected()
button_A = machine.Pin(0, machine.Pin.IN)
button_B = machine.Pin(2, machine.Pin.IN)
mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()

# set up values
REG_X0 = 0x32
REG_Y0 = 0x34
REG_ID = 0x00
REG_ON = 0x2d
g_earth = 9.8
multiplier = 0.004
message = 'test'
scroll_x = 0
scroll_y = 0
g_x = 0
g_y = 0
letter = ""
switch_state = 0

# switch input letters
def switch(self):
	global switch_state, letter
	print(switch_state)
	switch_state = switch_state % 9
	if switch_state == 0: letter = "C"## set time (hour)
	elif switch_state == 1: letter = "O"## set time (minute)
	elif switch_state == 2: letter = "L"## turn on alarm
	elif switch_state == 3:  letter = "U"## set alarm (hour)
	elif switch_state == 4: letter = "M"## set alarm (minute)
	elif switch_state == 5: letter = "B"## display weather
	elif switch_state == 6: letter = "I"## display last tweet
	elif switch_state == 7: letter = "A"## gesture recognition
	elif switch_state == 8: letter = ""## gesture recognition
	switch_state = switch_state + 1

# display message
def display_message(message_1= '', message_2 = '', message_3 = '', sleep_time = 0):
	global message1, message2, message3, oled
	oled.fill(0)
	oled.contrast(255 - min(255, int(adc.read())))
	if message_1 == '':
		oled.text(message1, 0, 0)
	else:
		oled.text(message_1, 0, 0)
		message1 = message_1
	if message_2 == '':
		oled.text(message2, 0, 10)
	else:
		oled.text(message_2, 0, 10)
		message2 = message_2
	if message_3 == '':
		oled.text(message3, 0, 20)
	else:
		oled.text(message_3, 0, 20)
		message3 = message_3
	oled.show()
	if sleep_time > 0:
		time.sleep(sleep_time)
		oled.fill(0)
		oled.show()

# write data
def write_data(location, value):
	location = ustruct.pack('B', location)
	value = ustruct.pack('B', value)
	cs.value(0)
	spi.write(location)
	spi.write(value)
	cs.value(1)

# read data
def read_data(location):
	location = location | 0x80
	location = ustruct.pack('B', location)
	cs.value(0)
	spi.write(location)
	buf = spi.read(1)
	cs.value(1)
	print(buf)

# read multi-byte data
def read_multidata(location):
	location = location | 0x80
	location = location | 0x40
	location = ustruct.pack('B', location)
	cs.value(0)
	spi.write(location)
	buf = spi.read(2)
	cs.value(1)
	return buf

# initialize adxl345
def init():
	read_data(REG_ID)
	read_data(REG_ON)
	read_data(0x31)
	write_data(REG_ON, 0x08)
	read_data(REG_ON)

# get x-axis reading
def get_x():
	temp = read_multidata(REG_X0)
	temp = ustruct.unpack('h', temp)
	return temp[0] * multiplier * g_earth

# get y-zxis reading
def get_y():
	temp = read_multidata(REG_Y0)
	temp = ustruct.unpack('h', temp)
	return temp[0] * multiplier * g_earth

button_A.irq(trigger = (machine.Pin.IRQ_RISING), handler = switch)

# main function
init()
while True:
	g_x = get_x()
	g_y = get_y()
	x = [0]
	y = [0]
	oled.fill(0)
	seq_x = ('X_axis: ', str(g_x))
	seq_y = ('Y_axis: ', str(g_y))
	oled.text(''.join(seq_x), 0, 0)
	oled.text(''.join(seq_y), 0, 10)
	if (letter is not ""): oled.text(letter, 0, 20)
	elif (prediction is not ""): oled.text(prediction["response"], 0, 20)
	oled.show()
	if (abs(g_x) >0.2 or abs(g_y)>0.2):
		print('start recording.')
		trigger = 0
		for i in range(1,100):
			g_x = get_x()
			g_y = get_y()
			if abs(g_x) < 0.08: g_x = 0
			if abs(g_y) < 0.08: g_y = 0
			if (abs(g_x) <0.08 and abs(g_y)<0.08 and trigger == 0): trigger = i
			seg_g = ('Time ', str(i), ' , X_axis: ', str(g_x), ' , Y_axis: ', str(g_y))
			print(''.join(seg_g))
#			x.append(g_x + x[i - 1])
#			y.append(g_y + y[i - 1])
			x.append(g_x)
			y.append(g_y)
		print(trigger)
		print(x)
		print(y)
		headers = {'Content-Type': 'application/json'}
		data = {"type": letter, "X": x, "Y": y}
		results = urequests.post('http://34.212.83.225:80', data=json.dumps(data), headers=headers)
		if (letter is ""):
			json_results = '{' + results.text.split('{', 1)[1].split('}')[0] + '}'
			json_results = json_results.replace("\'", "\"")
			prediction = json.loads(json_results)
			print(prediction["response"])
			oled.text(prediction["response"], 0, 20)
			oled.show()
		time.sleep(2)