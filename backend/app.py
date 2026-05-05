import os
import threading
import paho.mqtt.client as mqtt
import mysql.connector
from flask import Flask, jsonify

# ── Configuración ────────────────────────────
MQTT_HOST  = 'emqx'
MQTT_PORT  = 1883
MQTT_TOPIC = 'test01'

DB = {
    'host':     'mariadb',
    'user':     os.environ['MYSQL_USER'],
    'password': os.environ['MYSQL_PASSWORD'],
    'database': os.environ['MYSQL_DATABASE'],
}

# ── Base de datos ────────────────────────────
def get_conn():
    return mysql.connector.connect(**DB)

def init_db():
    conn = get_conn()
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS lecturas (
            id        INT AUTO_INCREMENT PRIMARY KEY,
            valor     FLOAT     NOT NULL,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# ── MQTT ─────────────────────────────────────
def on_message(client, userdata, msg):
    try:
        valor = float(msg.payload.decode().strip())
        conn  = get_conn()
        cur   = conn.cursor()
        cur.execute("INSERT INTO lecturas (valor) VALUES (%s)", (valor,))
        conn.commit()
        conn.close()
        print(f"Guardado: {valor}")
    except Exception as e:
        print(f"Error: {e}")

def start_mqtt():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT)
    client.subscribe(MQTT_TOPIC)
    client.loop_forever()

# ── Flask ────────────────────────────────────
app = Flask(__name__)

@app.route('/api/data')
def data():
    conn = get_conn()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT valor, creado_en FROM lecturas ORDER BY id DESC LIMIT 60")
    rows = cur.fetchall()
    conn.close()
    return jsonify(list(reversed(rows)))

# ── Arranque ─────────────────────────────────
if __name__ == '__main__':
    init_db()
    threading.Thread(target=start_mqtt, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
