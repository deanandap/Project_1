import dht
import network
import ntptime
import ujson
import utime

from machine import RTC
from machine import Pin

from third_party import rd_jwt

from umqtt.simple import MQTTClient


# Konstanta-konstanta aplikasi

# WiFi AP Information
AP_SSID = "V2027"
AP_PASSWORD = "lonbeh11"

# Decoded Private Key
PRIVATE_KEY = (26431011675321115380909776181103709066263183190983695305237073203523772865389235563567797800430085270490751170772131488280859777239103399945894006526610581426132223083777314070674104253438320680397506483082829102937947044964546500136476223491606079224935869726024110295157547468467623920908373307831919744215126010434725018337686253429221387139227388243450152586107014198316541280670165318323872350391695968059004097423408382785237501413169694043102411071047612622421427822953734334011878824894673029426122638010814063608617311214646186209035119700241759321948643643260985379152326596439755086966312609413917938643609, 65537, 20229078453735017263394013510962981873669759154013018185382094920663883350703551682759314125940654089789669773940817298940745617994967536473840692637262312186297300420513393906815118105012629919100027887833614980457825134326818253816096417201206483785396925242041035572192920388038322600192915402712075048446987079588032223460287501173242616556399348436276360008197692321118573749942364789541313548656405536967308090130115921390526705832496383848504683614136594980219833784782956461463982444241456093350864899201113848516471641056304301370558723245119594212112785350850576875851227314107898922086089160661737231149453, 166219710626179376174114275530287512237232910192936810444258249502652848268239161612445804758278241939810014714973198055372135035465548765167123179554768329296599664875968387426465720870801002096538605992320844905366341541287484633177752995923955962358825294136001593012053163047271595495779757836839077876031, 159012499635276511765095464805727883997988454566575893343487987946487410651636852455578820633021991032241186860084796162091911561134526500059902616274637685762894173083634930915941674205647820508562223391060488979293116847205568560400379018849535533691462848841998544954008067562036878564453676906765000486439)



#Project ID of IoT Core
PROJECT_ID = "hsc2020-05"
# Location of server
REGION_ID = "asia-east1"
# ID of IoT registry
REGISTRY_ID = "NPM_1704111010021"
# ID of this device
DEVICE_ID = "esp32"

# MQTT Information
MQTT_BRIDGE_HOSTNAME = "mqtt.googleapis.com"
MQTT_BRIDGE_PORT = 8883


dht22_obj = dht.DHT22(Pin(4))

def read_dht22():
    # Read temperature from DHT 22
    #
    # Return
    #    * List (temperature, humidity)
    #    * None if failed to read from sensor
    
    try:
        dht22_obj.measure()
        return dht22_obj.temperature(), dht22_obj.humidity()
    except:
        return None
    
    

def connect():
    # Connect to WiFi
    print("Connecting to WiFi...")
    
    # Activate WiFi Radio
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # If not connected, try tp connect
    if not wlan.isconnected():
        # Connect to AP_SSID using AP_PASSWORD
        wlan.connect(AP_SSID, AP_PASSWORD)
        # Loop until connected
        while not wlan.isconnected():
            pass
    
    # Connected
    print("  Connected:", wlan.ifconfig())


def set_time():
    # Update machine with NTP server
    print("Updating machine time...")

    # Loop until connected to NTP Server
    while True:
        try:
            # Connect to NTP server and set machine time
            ntptime.settime()
            # Success, break out off loop
            break
        except OSError as err:
            # Fail to connect to NTP Server
            print("  Fail to connect to NTP server, retrying (Error: {})....".format(err))
            # Wait before reattempting. Note: Better approach exponential instead of fix wiat time
            utime.sleep(0.5)
    
    # Succeeded in updating machine time
    print("  Time set to:", RTC().datetime())


def on_message(topic, message):
    print((topic,message))


def get_client(jwt):
    #Create our MQTT client.
    #
    # The client_id is a unique string that identifies this device.
    # For Google Cloud IoT Core, it must be in the format below.
    #
    client_id = 'projects/{}/locations/{}/registries/{}/devices/{}'.format(PROJECT_ID, REGION_ID, REGISTRY_ID, DEVICE_ID)
    client = MQTTClient(client_id.encode('utf-8'),
                        server=MQTT_BRIDGE_HOSTNAME,
                        port=MQTT_BRIDGE_PORT,
                        user=b'ignored',
                        password=jwt.encode('utf-8'),
                        ssl=True)
    client.set_callback(on_message)

    try:
        client.connect()
    except Exception as err:
        print(err)
        raise(err)

    return client


def publish(client, payload):
    # Publish an event
    
    # Where to send
    mqtt_topic = '/devices/{}/{}'.format(DEVICE_ID, 'events')
    
    # What to send
    payload = ujson.dumps(payload).encode('utf-8')
    
    # Send    
    client.publish(mqtt_topic.encode('utf-8'),
                   payload,
                   qos=1)
    

# Connect to Wifi
connect()
# Set machine time to now
set_time()

# Create JWT Token
print("Creating JWT token.")
start_time = utime.time()
jwt = rd_jwt.create_jwt(PRIVATE_KEY, PROJECT_ID)
end_time = utime.time()
print("  Created token in", end_time - start_time, "seconds.")

# Connect to MQTT Server
print("Connecting to MQTT broker...")
start_time = utime.time()
client = get_client(jwt)
end_time = utime.time()
print("  Connected in", end_time - start_time, "seconds.")

# Read from DHT22
print("Reading from DHT22")
result = read_dht22()
print("  Temperature:", result)

# Publish a message
print("Publishing message...")
if result == None:
    result = "Fail to read sensor...."
publish(client, result)
# Need to wait because command not blocking
utime.sleep(1)

# Disconnect from client
client.disconnect()