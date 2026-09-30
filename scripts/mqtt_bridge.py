"""Optional transport adapter. Install paho-mqtt; topic payload follows Observation schema."""
import json,os,urllib.request
import paho.mqtt.client as mqtt
BASE=os.getenv('SKYGUARD_URL','http://127.0.0.1:8010')
def on_connect(client,userdata,flags,reason_code,properties):
    if reason_code==0:client.subscribe(os.getenv('MQTT_TOPIC','skyguard/observations'),qos=1)
def on_message(client,userdata,message):
    try:
        body=json.loads(message.payload);body['source']='mqtt'
        req=urllib.request.Request(BASE+'/api/v1/observations',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-API-Key':os.getenv('SKYGUARD_API_KEY','')})
        with urllib.request.urlopen(req,timeout=20) as response: response.read()
        client.ack(message.mid,message.qos)
    except Exception as exc:print(json.dumps({'event':'mqtt_ingestion_failed','error':str(exc)}),flush=True)
client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id=os.getenv('MQTT_CLIENT_ID','skyguard-bridge'),manual_ack=True)
client.on_connect=on_connect;client.on_message=on_message
if os.getenv('MQTT_USERNAME'):client.username_pw_set(os.environ['MQTT_USERNAME'],os.getenv('MQTT_PASSWORD'))
if os.getenv('MQTT_TLS','true').lower()=='true':client.tls_set()
client.connect(os.environ['MQTT_HOST'],int(os.getenv('MQTT_PORT','8883')))
client.loop_forever()
