import dht
import network
import ntptime
import ujson
import utime

from machine import RTC
from machine import Pin
from time import sleep
from third_party import rd_jwt

from umqtt.simple import MQTTClient


# Konstanta-konstanta aplikasi

# WiFi AP Information
AP_SSID = "V2027"
AP_PASSWORD = "lonbeh11"

# Decoded Private Key
PRIVATE_KEY = (26431011675321115380909776181103709066263183190983695305237073203523772865389235563567797800430085270490751170772131488280859777239103399945894006526610581426132223083777314070674104253438320680397506483082829102937947044964546500136476223491606079224935869726024110295157547468467623920908373307831919744215126010434725018337686253429221387139227388243450152586107014198316541280670165318323872350391695968059004097423408382785237501413169694043102411071047612622421427822953734334011878824894673029426122638010814063608617311214646186209035119700241759321948643643260985379152326596439755086966312609413917938643609)

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
led_obj = Pin(23, Pin.OUT)
def suhu_kelembaban():
    # Read temperature from DHT 22
    #
    # Return
    #    * List (temperature, humidity)
    #    * None if failed to read from sensor
    while True:
        try:
            dht22_obj.measure()
            return dht22_obj.temperature(),dht22_obj.humidity()
            sleep(3)
            break
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
    
    
def subscribe_command3():
    print("Sending command to device")
    client_id = 'projects/{}/locations/{}/registries/{}/devices/{}'.format(PROJECT_ID, REGION_ID, REGISTRY_ID, DEVICE_ID)
    #ukur = f"/devices/{DEVICE_ID}/commands/#"
    command = 'Baca Kelembaban'
    data = command.encode("utf-8")
    while True:
        dht22_obj.measure()
        humi = dht22_obj.humidity()
        print(humi)
        sleep(3)
    publish(client, humi)
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
#print("Reading from DHT22")
#result1 = suhu_kelembaban()
#print("Suhu dan Kelembaban ", result1)
# Publish a message
#print("Publishing message...")
#if result1 == None:
  #result1 = "Fail to read sensor...."


#publish(client, result1)
# Need to wait because command not blocking
utime.sleep(1)

# Disconnect from client
client.disconnect()
#publish_events()
#publish_state()
#subscribe_config()
#subscribe_command()
#subscribe_command1()
#subscribe_command2()
subscribe_command3()
