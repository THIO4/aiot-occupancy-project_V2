import os
import json
from datetime import datetime
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

# Tuodaan tietokantafunktiot omasta moduulistaan
from db import init_db, insert_record

load_dotenv()

# MQTT credentials and settings
USERNAME = os.getenv("MQTT_USER")
PASSWORD = os.getenv("MQTT_PASS")
HOST = os.getenv("MQTT_HOST")
PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC = os.getenv("MQTT_TOPIC")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        client.subscribe(TOPIC)
    else:
        print(f"Connection failed with code {rc}")



def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode().strip()
        data = json.loads(payload)
        
        # Poimitaan arvot JSONista
        occupancy = data.get("person count")
        device_id = data.get("id")      # Tämä poimii "robo/aiot"
        timestamp = data.get("DateTime") # Tämä poimii "13 Jan 2026 9:36:7"
        
        # Jos viestissä ei ollut aikaleimaa, luodaan se itse
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        if occupancy is not None:
            # Varmista, että insert_record saa device_id:n (eli "robo/aiot")
            insert_record(timestamp, device_id, msg.topic, occupancy)
            print(f"Tallennettu: ID={device_id}, Occupancy={occupancy}")
            
    except Exception as e:
        print(f"Virhe: {e}")

def main():
    # Alustetaan tietokanta db.py:n funktiolla
    init_db()
    
    client = mqtt.Client(client_id="occupancy_collector")
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    
    print(f"Connecting to {HOST}...")
    client.connect(HOST, PORT, keepalive=60)
    client.loop_forever()

if __name__ == "__main__":
    main()