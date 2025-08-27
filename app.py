from flask import Flask, render_template
import mysql.connector
import requests
import json
from datetime import datetime, timedelta
import re
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Config DB (usa tu misma tabla 'saludos_diarios')
db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_URL = 'https://api.openai.com/v1/chat/completions'
OPENAI_MODEL = 'gpt-3.5-turbo'  # Como en tu PHP, modelo económico

# Función extraer salmo (regex como en PHP)
def extraer_salmo(texto):
    match = re.search(r'Salmo\s+(\d+)', texto, re.IGNORECASE)
    return int(match.group(1)) if match else None

# Obtener salmos usados última semana
def get_salmos_usados_ultima_semana(conn):
    fecha_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    cursor = conn.cursor()
    query = """
        SELECT salmo_dias, salmo_tardes, salmo_noches FROM saludos_diarios 
        WHERE fecha > %s AND fecha < %s
    """
    cursor.execute(query, (fecha_inicio, fecha_hoy))
    salmos = set()
    for row in cursor.fetchall():
        salmos.update(filter(None, row))
    cursor.close()
    return list(salmos)

# Prompt base (igual que PHP)
prompt_base = '''Genera tres saludos breves para nosotros en primera persona del plural. Cada uno adaptado a una parte del día:
1. Para buenos días (mañana, entre 0:00 y 11:59).
2. Para buenas tardes (tarde, entre 12:00 y 17:59).
3. Para buenas noches (noche, entre 18:00 y 23:59).
Cada saludo debe incorporar de forma natural una cita directa de un verso o fragmento reflexivo de un salmo católico diferente y poco común (como el Salmo 131, 138, 84, 119, 16, 42 u otros similares, evitando los más conocidos como el 23 o 91%s). Incluye la cita entre comillas, mencionando el salmo y versos (ejemplo: "Aún en la noche me instruye mi conciencia; tengo siempre presente al Señor: con Él a mi derecha no vacilaré" (Salmo 16,7-8)), y úsala para inspirar un tono esperanzador en el saludo para desear un buen [día/tarde/noche]. El saludo debe fluir naturalmente, integrando la cita como parte del mensaje, no solo mencionando el salmo por número. Que los saludos sean breves para nosotros en primera persona del plural
Formato de respuesta exacto:
Buenos días: [saludo completo aquí]
Buenas tardes: [saludo completo aquí]
Buenas noches: [saludo completo aquí]'''

# Generar saludos con OpenAI
def generate_saludos(salmos_usados):
    evitar_str = ''
    if salmos_usados:
        evitar_str = ', y evita estrictamente usar estos salmos que ya se usaron recientemente: ' + ', '.join(map(str, salmos_usados))
    prompt = prompt_base % evitar_str

    data = {
        'model': OPENAI_MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.8,
        'max_tokens': 450
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }

    response = requests.post(OPENAI_URL, json=data, headers=headers)
    if response.status_code == 200:
        content = response.json()['choices'][0]['message']['content'].strip()
        lines = content.split('\n')
        saludos = {'dias': '', 'tardes': '', 'noches': ''}
        for line in lines:
            if line.startswith('Buenos días:'):
                saludos['dias'] = line[len('Buenos días:'):].strip()
            elif line.startswith('Buenas tardes:'):
                saludos['tardes'] = line[len('Buenas tardes:'):].strip()
            elif line.startswith('Buenas noches:'):
                saludos['noches'] = line[len('Buenas noches:'):].strip()
        return saludos
    else:
        return {'dias': 'Error', 'tardes': 'Error', 'noches': 'Error'}

# Obtener o generar saludos del día
def get_saludos_del_dia():
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM saludos_diarios WHERE fecha = %s"
    cursor.execute(query, (fecha_hoy,))
    row = cursor.fetchone()

    if row:
        cursor.close()
        conn.close()
        return {
            'dias': row['saludo_dias'],
            'tardes': row['saludo_tardes'],
            'noches': row['saludo_noches']
        }
    else:
        salmos_usados = get_salmos_usados_ultima_semana(conn)
        saludos = generate_saludos(salmos_usados)
        salmo_dias = extraer_salmo(saludos['dias'])
        salmo_tardes = extraer_salmo(saludos['tardes'])
        salmo_noches = extraer_salmo(saludos['noches'])

        insert_query = """
            INSERT INTO saludos_diarios (fecha, saludo_dias, saludo_tardes, saludo_noches, salmo_dias, salmo_tardes, salmo_noches)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (fecha_hoy, saludos['dias'], saludos['tardes'], saludos['noches'], salmo_dias, salmo_tardes, salmo_noches))
        conn.commit()
        cursor.close()
        conn.close()
        return saludos

@app.route('/')
def index():
    saludos = get_saludos_del_dia()
    # Determinar saludo actual basado en hora del servidor (mejoraremos con JS en UI)
    hora = datetime.now().hour
    if hora < 12:
        etiqueta = 'Buenos días'
    elif hora < 18:
        etiqueta = 'Buenas tardes'
    else:
        etiqueta = 'Buenas noches'
    return render_template('index.html', saludos=saludos, etiqueta=etiqueta)

if __name__ == '__main__':
    app.run(debug=True, port=5002)