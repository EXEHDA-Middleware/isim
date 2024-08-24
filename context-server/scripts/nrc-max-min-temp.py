import mysql.connector
import os
import sys
from dotenv import load_dotenv
import subprocess
from datetime import datetime, tzinfo
import requests
import threading
import time

load_dotenv()

host = os.getenv("MYSQL_INTERNAL_DB_HOST")
usr = os.getenv("MYSQL_INTERNAL_DB_USER")
passw = os.getenv("MYSQL_INTERNAL_DB_PASSWORD")
db = os.getenv("MYSQL_INTERNAL_DB_NAME")

if len(sys.argv) < 3:
    print(
        "To run the script use: python3 context-server/scripts/nrc-max-min-temp.py <SENSOR_ID> <PROJECT>"
    )
    sys.exit(1)
else:
    sensor_id = sys.argv[1]
    project = sys.argv[2]

i2mf_conn = mysql.connector.connect(host=host, user=usr, password=passw, database=db)
i2mf_cursor = i2mf_conn.cursor()

i2mf_cursor.execute(
    "SELECT host, user, password, `database` FROM projects WHERE origin = %s",
    (project,),
)
project_data = i2mf_cursor.fetchone()

i2mf_conn.close()

conn = mysql.connector.connect(
    host=project_data[0],
    user=project_data[1],
    password=project_data[2],
    database=project_data[3],
)
cursor = conn.cursor()

# Execute the SQL query to retrieve the maximum and minimum temperature for the given sensor ID
query = """
    SELECT data, sensors.name 
    FROM sensor_data 
    LEFT JOIN sensors ON sensor_data.sensor_id = sensors.id  
    WHERE sensor_id = %s 
    ORDER BY gathered_at DESC 
    LIMIT 1
"""
cursor.execute(query, (sensor_id,))
result = cursor.fetchone()

if result is None:
    print("No data found for the given sensor ID")
    sys.exit(1)

sensor_data = float(result[0])
sensor_name = result[1]
alert_msg = []

print("Sensor data:", sensor_data)

print(sensor_data >= 25.0)

data_e_hora_atuais = datetime.now()
if sensor_data >= 25.0:
    alert_msg.append(
        "ALERTA ⚠️ "
        + data_e_hora_atuais.strftime("%d/%m/%Y %H:%M")
        + " - %s: %s ºC" % (sensor_name, str(sensor_data))
    )
else:
    hora, minuto = time.localtime()[3], time.localtime()[4]

    if ((hora == 12) and (minuto <= 5)) or ((hora == 11) and (minuto > 57)):
        alert_msg.append(
            "Diaria 🟢 "
            + data_e_hora_atuais.strftime("%d/%m/%Y %H:%M")
            + " - %s: %s ºC" % (sensor_name, str(sensor_data))
        )

for msg in alert_msg:
    time.sleep(1)
    requests.post(
        "https://ntfy.sh/i2mf-exehda", data=msg.encode(encoding="utf-8")
    )  # TODO: create custom json field on project table to store notifications credentials


# Close the database connection
conn.close()
