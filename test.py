import network
import json
from time import sleep

import Http

server = Http.Server()

# GET http://ip_address
@server.route()
def root(request):
    return Http.HtmlResponse('This is the root page')

# GET http://ip_address/test?test=my_value
@server.route("GET", "/test")
def test(request):
    r = 'No value'
    if 'test' in request.params:
        r = request.params['test']
    return Http.HtmlResponse(f'Test value: {r}')

# PUT http://ip_address/test with any text data in the body
@server.route("PUT", "/test")
def testput(request):
    r = str(request.data, 'utf-8')
    return Http.HtmlResponse(f'Test data: {r}')

# GET http://ip_address/filetest
# Returns this file
@server.route("GET", "/filetest")
def filetest(request):
    return Http.FileResponse('test.py')

# GET http://ip_address/json
# and this function returns {"test": true}
@server.route("GET", "/json")
def root(request):
    resp = json.loads('{"test": true}')
    return Http.JsonResponse(resp)

# PUT http://ip_address/addone with data {"count": 144}
# and this function returns {"count": 145}
@server.route("PUT", "/addone")
def addone(request):
    resp = request.jsonData()
    resp['count'] += 1
    return Http.JsonResponse(resp)

# WiFi/network
ssid = 'your_wifi_name'
password = 'your_wifi_password'
wlan = network.WLAN(network.STA_IF)
print(f'Connecting to wlan {ssid}...')
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    sleep(.1)

if wlan.status() < 0:
    ws = wlan.status()
    print(f'Error connecting to wlan: {ws}')
else:
    ip = wlan.ifconfig()[0]
    print(f'wlan connected at ip {ip}')
    server.start()

print('Start main loop')
while True:
    server.checkRequest()	# Make sure this function get called regularly from the main loop
    sleep(.1)