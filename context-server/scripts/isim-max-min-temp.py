import mysql.connector
import os
import sys
from dotenv import load_dotenv
import subprocess
from datetime import datetime, tzinfo, timedelta
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
    SELECT data, sensors.name, gathered_at
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
sensor_gathered_at = result[2]

alert_msg = []

# print("Sensor data:", sensor_data)

# print(sensor_data >= 25.0)

# def convert_utc_to_utc_minus_3(utc_time):
# Assuming utc_time is a datetime object in UTC
# utc_minus_3_time = utc_time - timedelta(hours=3)
# return utc_minus_3_time

# Example usage
# utc_time = datetime.utcnow()  # Current UTC time
# utc_minus_3_time = convert_utc_to_utc_minus_3(utc_time)

# print(f"UTC Time: {utc_time}")
# print(f"UTC-3 Time: {utc_minus_3_time}")

# data_e_hora_atuais = utc_minus_3_time
data_e_hora_atuais = sensor_gathered_at - timedelta(hours=3)

# data_e_hora_atuais = datetime.now()
if sensor_data >= 30.0:
    alert_msg.append(
        "ALERTA ⚠️ "
        + data_e_hora_atuais.strftime("%d/%m/%Y %H:%M")
        + " - %s: %s ºC" % (sensor_name, str(round(sensor_data, 1)))
    )
else:
    #    hora, minuto = time.localtime()[3], time.localtime()[4]
    hora = int(data_e_hora_atuais.strftime("%H"))
    minuto = int(data_e_hora_atuais.strftime("%M"))
    #    print(hora)
    #    print(minuto)

    if ((hora == 12) and (minuto < 5)) or ((hora == 11) and (minuto > 55)):
        alert_msg.append(
            "Diaria 🟢 "
            + data_e_hora_atuais.strftime("%d/%m/%Y %H:%M")
            + " - %s: %s ºC" % (sensor_name, str(round(sensor_data, 1)))
        )

# alert_msg.append(
#      "Diaria 🟢 "
#      + data_e_hora_atuais.strftime("%d/%m/%Y %H:%M")
#      + " - %s: %s ºC" % (sensor_name, str(sensor_data))
#      )

for msg in alert_msg:
    time.sleep(1)
    requests.post(
        #        "https://ntfy.sh/nrc-adenauer", data=msg.encode(encoding="utf-8")
        "https://ntfy.sh/i2mf-isim",
        data=msg.encode(encoding="utf-8"),
    )  # TODO: create custom json field on project table to store notifications credentials


# Close the database connection
conn.close()
