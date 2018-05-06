# Lab 6: Checkpoint 4&5
# Group 9: Zhifu Xiao (zx2201), Chen Zhao(cz2498), Chuhan Li(cl3619)

# import modules
import socket 
import machine
import network
import urequests
import ubinascii
import ssd1306
from ntptime import settime
import utime
import network
import json
import ustruct
import time
import gc

# set up values
rtc = machine.RTC()
i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))
oled = ssd1306.SSD1306_I2C(128, 32, i2c)
spi = machine.SPI(1, baudrate=500000, polarity=1, phase=1)
spi.init()
cs = machine.Pin(16, machine.Pin.OUT)
cs.value(0)
adc = machine.ADC(0)
button_A = machine.Pin(0, machine.Pin.IN)
button_B = machine.Pin(2, machine.Pin.IN)
sound = machine.PWM(machine.Pin(15))
sound.freq(60)
tim = machine.Timer(1)
message1 = ''
message2 = ''
message3 = ''
REG_X0 = 0x32
REG_Y0 = 0x34
REG_ID = 0x00
REG_ON = 0x2d
g_earth = 9.8
multiplier = 0.004
scroll_x = 0
scroll_y = 0
g_x = 0
g_y = 0
switch_state = -1
_hextobyte_cache = None
alarm = False
stop = False
headers = {'Content-Type': 'application/json'}

html_header = """
<!DOCTYPE html>
<html>
<head> <title>Response</title> </head>
<form>
Command: 
"""

html_middle = """
<br><br>
Response: 
"""

html_end = """
</form>
</html>
"""

# switch function
def switch(self):
	global switch_state, stop
	switch_state = switch_state + 1
	switch_state = switch_state % 6
	if switch_state == 0:
		display_message(message_1= 'set time (hour)')
	elif switch_state == 1:
		display_message(message_1= 'set time (minute)')
	elif switch_state == 2:
		display_message(message_1= 'set alarm (hour)')
	elif switch_state == 3:
		display_message(message_1= 'set alarm (minute)')
	elif switch_state == 4:
		display_message(message_1= 'turn on/off alarm')
	elif switch_state == 5:
		display_message(message_1= 'gesture recognition')
		stop = False
		gesture_reco()

# action function
def action(self):
	global switch_state, alarm, stop
	switch_state = switch_state % 6
	if switch_state == 0:
		set_time(method = 1)
	elif switch_state == 1:
		set_time(method = 2)
	elif switch_state == 2:
		set_time(method = 3)
	elif switch_state == 3:
		set_time(method = 4)
	elif switch_state == 4:
		alarm = not alarm
		display_message(message_1 = str(alarm))
	elif switch_state == 5:
		stop = not stop

# display function with check alarm
def display_message(message_1= '', message_2 = '', message_3 = '', sleep_time = 0):
	global message1, message2, message3, oled, alarm, alarm_time
	gc.collect()
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
	if alarm:
		print(alarm_time)
		print(rtc.datetime()[4:7])
		if alarm_time[0:2] == rtc.datetime()[4:6] and abs(rtc.datetime()[6] - alarm_time[2]) <= 3:
			print('Alarm!')
			oled.fill(0)
			oled.text('Time is up!', 0, 0)
			oled.show()
			sound.duty(100)
			time.sleep(2)
			sound.duty(0)
			alarm = False

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

# get X
def get_x():
	temp = read_multidata(REG_X0)
	temp = ustruct.unpack('h', temp)
	return temp[0] * multiplier * g_earth

# get Y
def get_y():
	temp = read_multidata(REG_Y0)
	temp = ustruct.unpack('h', temp)
	return temp[0] * multiplier * g_earth

# get weather information
def send_weather():
	global lat, lng
	seq_weather = ('http://api.openweathermap.org/data/2.5/weather?lat=', lat, '&lon=', lng, '&APPID=0b454e72677fd394670999db2280260a')
#	url_weather = 'http://api.openweathermap.org/data/2.5/weather?lat=40.8139&lon=-73.962&APPID=0b454e72677fd394670999db2280260a'
	url_weather = ''.join(seq_weather)
	resp_weather = urequests.post(url_weather)
	desp_weather = resp_weather.json()['weather'][0]['main'].lower()
	seq_weather = (desp_weather, ', ', str(round(resp_weather.json()['main']['temp']-273.15, 2)), 'C')
	return ''.join(seq_weather)
	
# send twitter
def send_tweet(content):
	data_ifttt = json.dumps({'value1': content})
	url_ifttt = 'http://maker.ifttt.com/trigger/send_custom_tweet/with/key/Jv-Z6azK9xnE6H6Rh6wGw'
	resp_ifttt = urequests.post(url_ifttt, data = data_ifttt, headers = headers)
	return resp_ifttt.text

# gesture recognition
def gesture_reco():
	global stop, headers
	while not stop: 
		g_x = get_x()
		g_y = get_y()
		x = [0]
		y = [0]
		if (abs(g_x) >0.2 or abs(g_y)>0.2):
			print('start recording.')
			for i in range(1,100):
				x.append(get_x())
				y.append(get_y())
				time.sleep(0.01)
			print('finished recording.')
			data = {"X": x, "Y": y}
			
			results = urequests.post('http://34.212.83.225:80', data=json.dumps(data), headers=headers)
			results_loc = results.text.find('}') - 2
			display_message(message_3 = results.text[results_loc:results_loc + 1])
			stop = not stop
	gc.collect()
	
# set time
def set_time(method):
	global alarm_time, rtc
	if method == 1:
		temp = list(rtc.datetime())
		temp[4] = temp[4] + 1
		rtc.datetime(tuple(temp))
		display_message(message_1 = str(rtc.datetime()[4:7]))
	elif method == 2:
		temp = list(rtc.datetime())
		temp[5] = temp[5] + 1
		rtc.datetime(tuple(temp))
		display_message(message_1 = str(rtc.datetime()[4:7]))
	elif method == 3:
		temp = list(alarm_time)
		temp[0] = (temp[0] + 1) % 24
		alarm_time = tuple(temp)
		display_message(message_1 = str(alarm_time))
	elif method == 4:
		temp = list(alarm_time)
		temp[1] = (temp[1] + 1) % 60
		alarm_time = tuple(temp)
		display_message(message_1 = str(alarm_time))

button_A.irq(trigger = (machine.Pin.IRQ_RISING), handler = switch)
button_B.irq(trigger = (machine.Pin.IRQ_RISING), handler = action)
gc.threshold(1000)
read_data(REG_ID)
read_data(REG_ON)
read_data(0x31)
write_data(REG_ON, 0x08)
read_data(REG_ON)

sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
	print('connecting to network...')
	sta_if.active(True)
#	sta_if.connect('Columbia University', '')
	sta_if.connect('Zhifu\'s TC', 'b1ebb640e04e')

settime()
alarm_time = utime.localtime()[3:6]
display_input = ''

print('ready!')
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((sta_if.ifconfig()[0], 80))
print('network config:', sta_if.ifconfig())
s.listen(5)
feedback = ''
data = '{"wifiAccessPoints": {"macAddress": "5c:cf:7f:3a:d8:64"}}'
resp_location = urequests.post(url_location, data=data, headers=headers)
lat = str(resp_location.json()['location']['lat'])
lng = str(resp_location.json()['location']['lng'])
url_weather = 'http://api.openweathermap.org/data/2.5/weather?lat=40.8139&lon=-73.962&APPID=0b454e72677fd394670999db2280260a'
tim.init(period = 5000, mode = machine.Timer.PERIODIC, callback = lambda tim: display_message(message_3 = str(rtc.datetime()[4:7])))

while True:
	gc.collect()
	print("starting...")
	conn, addr = s.accept()
	print("Got a connection from %s" % str(addr))
	request = conn.recv(1024)
	print("Content = %s" % str(request))
	request = str(request)
	INPUT = request.find('/?Input=')
	if INPUT is not -1:
		display_input = request[INPUT+8:request.find('HTTP/1.1')-1].replace('%20', ' ')
		if (display_input.find('tweet') == 0):
			gc.collect()
			content = display_input.split('tweet', 1)[1].strip()
			feedback = send_tweet(content)
			display_message(message_2 = content)
		elif (display_input.find('weather') == 0):
			feedback = send_weather()
			display_message(message_2 = feedback)
		elif (display_input.find('time') == 0):
			feedback = rtc.datetime()[4:7]
			display_message(message_2 = str(feedback))
		print(display_input)
	response = ''.join((html_header, str(display_input), html_middle, str(feedback), html_end))
	conn.send(response)
	conn.close()