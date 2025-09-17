import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe('teste')

# The callback for when a PUBLISH message is received from the server.

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

    
mqttc = mqtt.Client(
    
    mqtt.CallbackAPIVersion.VERSION2,
    client_id='giovane',
    clean_session=False,

)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.connect("127.0.0.1", 1883, 60)
mqttc.loop_start()

while True:
    message=input("Manda sua mensagem: ")
    topico= 'teste'
    mqttc.publish(f"{topico}", message, retain=True, qos=1)
# 
mqttc.loop_stop()