"""ESP32 web based control module."""
import usocket as socket
from machine import Pin
from umqtt.robust import MQTTClient
from machine import Timer
import json
import my_config as mc

relay = Pin(3, Pin.OUT)

def sub_cb(topic, msg):
    """Changes relay state when message is received."""

    try:
        d = json.loads(msg)
        data = d["state"]["desired"]["relay state"]

        if data == "on":
            relay.value(1)
        else:
            relay.value(0)

        j = {
            "state": {
                "reported" : {
                    "relay state": data
                }
            }
        }

        client.publish(mc.SHADOW_UPDATE, json.dumps(j))
    except Exception as e:
        print(e)

# setup AWS SSL
KEY_PATH = "AWS-private.pem.key"
CERT_PATH = "AWS-certificate.pem.crt"
try:
    with open(KEY_PATH, "r") as f:
        key = f.read()
    with open(CERT_PATH, "r") as f:
        cert = f.read()
except Exception as e:
    print("Read SSL Certs", e)

# setup AWS parameters
CLIENT_ID = mc.ID
HOST = mc.AWS_HOST
PORT = 8883
SSL_PARAMS = {"key": key, "cert": cert, "server_side": False}

# setup MQTT
try:
    global client
    client = MQTTClient(client_id = CLIENT_ID,
                        server = HOST,
                        port = PORT,
                        keepalive = 10000,
                        ssl = True,
                        ssl_params = SSL_PARAMS)
    client.set_callback(sub_cb)
    client.connect()
    client.subscribe("$aws/things/Moisture_Monitor/shadow/update/accepted")
    print("Successfully connected to MQTT Broker.")
except Exception as e:
    print("Setup MQTT Error:", e)


def web_page():
    """Return HTML."""

    try:
        if relay.value() == 1:
            relay_state="ON"
        else:
            relay_state="OFF"

        html = ""
        with open("html_script.txt", "r") as myfile:
            html = myfile.read()
            html = html.replace("relay_state", relay_state)

    except Exception as e:
        print("Error:web_page:", e)
    return html


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

# Checks every second if there are any new messages
def read_message(tmrObj):
    client.check_msg()

tmr = Timer(-1)
tmr.init(mode=Timer.PERIODIC, period=1000, callback=read_message)


old_state = ""
new_state = ""
i = 0

while True:
    try:
        conn, addr = s.accept()
        print("Got a connection from %s" % str(addr))
        request = conn.recv(1024)
        request = str(request)
        # print("Content = %s" % request)
        relay_on = request.find("/?relay=on")
        relay_off = request.find("/?relay=off")
        if relay_on == 6:
            print("Relay On")
            new_state = "on"
            relay.value(1)
        if relay_off == 6:
            print("Relay Off")
            new_state = "off"
            relay.value(0)
        response = web_page()
        conn.send("HTTP/1.1 200 OK\n")
        conn.send("Content-Type: text/html\n")
        conn.send("Connection: close\n\n")
        conn.sendall(response)
        conn.close()

        if new_state != old_state:
            print("State has changed!")

            j = {
                "state": {
                    "reported" : {
                        "relay state": new_state
                    }
                }
            }

            client.publish(f"$aws/things/Moisture_Monitor/shadow/update", json.dumps(j))
        else:
            print("State has not changed.")

        if i > 5:
            break
        i = i + 1

        old_state = new_state

    except Exception as e:
        print("main loop:", e)
