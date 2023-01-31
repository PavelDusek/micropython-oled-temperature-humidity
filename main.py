import machine
import ssd1306
import time
import dht
import network
import ujson
import urequests

url = "https://www.timeapi.io/api/Time/current/zone?timeZone=Europe/Prague"
wifi_list = [
    #enter list of WLANs to try:
    ("<ssid1>", "<key1>"),
    ("<ssid2>", "<key2>"),
    ("<ssid3>", "<key3>"),
]
ssid, key = None, None
wifi_wait = 10

def try_connect(ssid, key):
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network {} with key {}'.format(ssid, key))
        sta_if.active(True)
        sta_if.connect(ssid, key)
        if not sta_if.isconnected():
            time.sleep(wifi_wait)
    print('network config:', sta_if.ifconfig())
    return sta_if.isconnected()

def measure():
    sensor = dht.DHT11(machine.Pin(2))
    time.sleep_ms(500)
    sensor.measure()
    tem = sensor.temperature()
    hum = sensor.humidity()
    return tem, hum

def setRTC(rtc, ssid, key):
    try_connect(ssid, key)
    try:
        r = urequests.get(url)
        json = ujson.loads(r.text)
        print(json)
        # (year, month, day, dayOfWeek!!!, hour, minute, second, millis)
        dayOfWeek = { 'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6, }
        rtc.datetime((
            json['year'],
            json['month'],
            json['day'],
            dayOfWeek[json['dayOfWeek']],
            json['hour'],
            json['minute'],
            json['seconds'],
            json['milliSeconds']
        ))
    except:
        pass

def oled_show(oled, text1, text2):
    oled.fill(0)
    oled.text(text1, 0,  0)
    oled.text(text2, 0, 10)
    oled.show()

########
# BODY #
########
i2c = machine.SoftI2C(scl = machine.Pin(5), sda = machine.Pin(4))
oled_width, oled_height = 128, 32 #128, 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

#try to find the wifi
for ssid_try, key_try in wifi_list:
    #try if wifi can be connected
    oled_show(oled, "Connecting", ssid_try)
    if try_connect(ssid_try, key_try):
        #set the right ssid and key
        ssid, key = ssid_try, key_try
        #if successful, do not try other ssid
        break

#try to set the chip datetime
rtc = machine.RTC()
setRTC(rtc, ssid, key)

while True:
    #set RTC every hour
    if ssid:
        #if known wifi, just use it
        setRTC(rtc, ssid, key)
    else:
        #if not known wifi, try to find it
        for ssid_try, key_try in wifi_list:
            #try if wifi can be connected
            if try_connect(ssid_try, key_try):
                #set the right ssid and key
                ssid, key = ssid_try, key_try
                #if successful, do not try other ssid
                break

    #for each minute in an hour, do measurements
    for _ in range(60):
        tem, hum = measure()
        co2 = "-"
        state1 = "{} oC {} %".format(tem, hum)
        state2 = "{} ppm".format(co2)

        oled.fill(0)
        if ssid:
            year, month, day, weekday, hour, minute, second, microsecond = rtc.datetime()
            now = "{}:{:02d} {}.{}.{}".format(hour, minute, day, month, year)
            oled.text(now,    0,  0)
        oled.text(state1, 0, 10)
        oled.text(state2, 0, 20)
        oled.show()
        time.sleep(60)
