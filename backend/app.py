import os
import ssl
import threading
import paho.mqtt.client as mqtt
import mysql.connector
from flask import Flask, jsonify

# ── Configuración MQTT ───────────────────────
MQTT_HOST  = os.environ.get('MQTT_HOST', 'localhost')
MQTT_PORT  = int(os.environ.get('MQTT_PORT', 8884))
MQTT_TOPIC = os.environ.get('MQTT_TOPIC', 'test01')
MQTT_USER  = os.environ.get('MQTT_USER', '')
MQTT_PASS  = os.environ.get('MQTT_PASS', '')

# ── Configuración MySQL ──────────────────────
DB = {
    'host':     os.environ.get('MYSQL_HOST') or os.environ.get('MYSQLHOST', 'localhost'),
    'port':     int(os.environ.get('MYSQL_PORT') or os.environ.get('MYSQLPORT', 3306)),
    'user':     os.environ.get('MYSQL_USER') or os.environ.get('MYSQLUSER', ''),
    'password': os.environ.get('MYSQL_PASSWORD') or os.environ.get('MYSQLPASSWORD', ''),
    'database': os.environ.get('MYSQL_DATABASE') or os.environ.get('MYSQLDATABASE', ''),
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
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado a HiveMQ")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Error de conexión MQTT, código: {rc}")

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
        print(f"Error al guardar: {e}")

def start_mqtt():
    # Usar WebSockets sobre TLS (puerto 8884) que Railway permite
    client = mqtt.Client(transport="websockets")
    client.on_connect = on_connect
    client.on_message = on_message
    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)
    client.connect(MQTT_HOST, MQTT_PORT)
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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))