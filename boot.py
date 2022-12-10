from ntptime import settime
import time
import network
import webrepl
import my_config as mc

def do_connect():
	wlan = network.WLAN(network.STA_IF)
	wlan.active(True)
	print('Connecting to network...')

	while not wlan.isconnected():
		wlan.connect(mc.WIFI_NAME, mc.WIFI_PW)
		time.sleep(5)
	print('Network config:', wlan.ifconfig())

do_connect()
webrepl.start()

settime()