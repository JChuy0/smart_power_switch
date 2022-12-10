"""A MQTT Client"""

import paho.mqtt.client as mqtt
import json
import ssl
import time
import my_config as mc

old_state = ""

def on_connect(client, userdata, flags, rc):
    """Event happens on connection to broker."""

    try:
        print(f"Successfully connected with result code: {rc}")
        client.subscribe(mc.SHADOW_GET_ACCEPTED)
        client.subscribe(mc.SHADOW_GET_REJECTED)
    except Exception as e:
        print(e)

def on_message(client, userdata, msg):
    """Event happens when recieved message from broker."""

    try:
        global old_state
        
        d = json.loads(msg.payload)
        new_state = d["state"]["reported"]["relay state"]

        # if relay state is not empty and state has changed, publish a message
        if new_state != "relay state" and new_state != old_state:
            j = {
                "state": {
                    "desired" : {
                        "relay state": new_state
                    }
                }
            }

            client.publish(mc.SHADOW_UPDATE, json.dumps(j))

            print(f"State is: {new_state}")
        
        print(f"Old state is: {old_state}, New state is: {new_state}.")
        old_state = new_state

    except Exception as e:
        print(e)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# setup SSL/TLS
client.tls_set(ca_certs = "AmazonRootCA1.pem",
                certfile = "AWS-certificate.pem.crt",
                keyfile = "AWS-private.pem.key",
                cert_reqs = ssl.CERT_REQUIRED,
                tls_version = ssl.PROTOCOL_TLS,
                ciphers = None)

# connect to AWS MQTT server
client.connect(mc.AWS_HOST, 8883, 60)
client.loop_start()


while True:
    client.publish(mc.SHADOW_GET, json.dumps({}))

    time.sleep(10)
