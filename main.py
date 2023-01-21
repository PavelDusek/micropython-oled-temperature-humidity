import machine
import ssd1306
import time
import dht
import network
import ujson
import urequests

url = "https://www.timeapi.io/api/Time/current/zone?timeZone=Europe/Prague"
ssid, key = "", ""

def do_connect(ssid, key):
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(ssid, key)
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())

def measure():
    sensor = dht.DHT11(machine.Pin(2))
    time.sleep_ms(500)
    sensor.measure()
    tem = sensor.temperature()
    hum = sensor.humidity()
    return tem, hum

########
# BODY #
########
i2c = machine.SoftI2C(scl = machine.Pin(5), sda = machine.Pin(4))
oled_width, oled_height = 128, 32
#oled_width, oled_height = 128, 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

do_connect(ssid, key)
rtc = machine.RTC()
r = urequests.get(url)
json = ujson.loads(r.text)
# (year, month, day, dayOfWeek!!!, hour, minute, second, millis)
dayOfWeek = { 'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6, }
rtc.datetime((json['year'], json['month'], json['day'], dayOfWeek[json['dayOfWeek']], json['hour'], json['minute'], json['seconds'], json['milliSeconds']))

while True:
    tem, hum = measure()
    co2 = "-"

    #year, month, day, hour, minute, seconds, weekday, yearday = time.localtime()
    #year, month, day, hour, minute, second, microsecond, tzinfo = rtc.datetime()
    year, month, day, weekday, hour, minute, second, microsecond = rtc.datetime()

    now = "{}:{:02d} {}.{}.{}".format(hour, minute, day, month, year)
    state1 = "{} oC {} %".format(tem, hum)
    state2 = "{} ppm".format(co2)

    oled.fill(0)
    oled.text(now,    0,  0)
    oled.text(state1, 0, 10)
    oled.text(state2, 0, 20)
    oled.show()
    time.sleep(60)
