#Temp and humidity check for dht11
#pico sends temp, humidity, and time via http
#to python anywhere server periodically
 
from machine import Pin, RTC
import utime as time
from dht import DHT11
import network
import urequests
import json
import socket
import struct

#Pin and temps
dataPin=16
myPin= Pin(dataPin,Pin.OUT,Pin.PULL_DOWN)
sensor=DHT11(myPin)

# For time sync via wifi
NTP_DELTA = 2208988800
host = "pool.ntp.org"

#Methods

def set_time():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(1)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()
    val = struct.unpack("!I", msg[40:44])[0]
    t = val - NTP_DELTA
    timezone_offset = -5
    t += timezone_offset * 3600  
    tm = time.gmtime(t)
    machine.RTC().datetime((
    tm[0], tm[1], tm[2], tm[6] + 1,
    tm[3], tm[4], tm[5], 0
    ))
    print(f"Time set to {time.localtime()}")
    long_blink(7)

def get_time():
    now = time.localtime()
    
    return now

def get_temp ():
    sensor.measure()
    now = get_time()
    print(f"Time: {now}")
    print(f"Temp: {sensor.temperature()}C")
    print(f"Humidity: {sensor.humidity()}")
    sensor_data = {'time' : now,
                   "temp": sensor.temperature(),
                   "humidity": sensor.humidity()
                   }
    print(f"sensor_data: {sensor_data}")
    return sensor_data

def connect_to_wifi():
    wlan = network.WLAN()
    wlan.active(True)
    long_blink(2)
    if not wlan.isconnected():
        print("Connecting to network...")
        #wlan.connect('network', 'password')
        while not wlan.isconnected():
            print("Attempting to connect...")
            long_blink(5)
            time.sleep(5)
        if wlan.status() !=3:
            raise RuntimeError("network connection failed")
        else:
            long_blink(2)
            print("Connected")
    print('network config:', wlan.ipconfig('addr4'))
    pico_ip = wlan.ipconfig('addr4')
    return pico_ip[0]

def post_data(sensor_data):
    print("Posting...")
    try:
        #Pythonanywhere server
        url = "https://kappa5400.pythonanywhere.com/test"
        headers = {'Content-Type': 'application/json'}
        response = urequests.post(url, headers=headers, json=sensor_data)
        print(f" Server response: {response.text}")
        long_blink(2)
        response.close()
    except Exception as e:
        print("Error posting:", e)
        blink()

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 80))
    s.listen(1)
    print("Server listening on port 80")
    return s

def handle_request():
    cl, addr = s.accept()
    print("Client connected from", addr)
    request = cl.recv(1024)
    request = request.decode()
    print('Request:', request)
    
def http_back():
    http_response = 'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n'
    http_response += json.dumps(sensor_data)
    client.send(http_response)

#For feedback
def blink():
    light = Pin('LED', Pin.OUT)
    light.value(1)
    time.sleep(.5)
    light.value(0)
    time.sleep(.5)

def long_blink(t):
    light = Pin('LED', Pin.OUT)
    light.value(1)
    time.sleep(t)
    light.value(0)
    time.sleep(t)

#Main

blink()
pico_ip = connect_to_wifi()
print(f"Pico I.P. {pico_ip}")
blink()
set_time()

while True:
    print("Starting...")
    long_blink(2)
    try:
        sensor_data = get_temp()
        post_data(sensor_data)
        blink()
        blink()
        
    except Exception as e:
        print("Error handling request:", e)
        
    long_blink(5)
    print("Sleeping 10 minutes...")
    time.sleep(600)
    
    



