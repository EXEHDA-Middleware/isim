import paho.mqtt.client as mqtt
import json
import datetime
import mysql.connector
import os
from dotenv import load_dotenv
import subprocess

script_dir = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

internal_host = os.getenv("MYSQL_INTERNAL_DB_HOST")
internal_usr = os.getenv("MYSQL_INTERNAL_DB_USER")
internal_passw = os.getenv("MYSQL_INTERNAL_DB_PASSWORD")
internal_db = os.getenv("MYSQL_INTERNAL_DB_NAME")

project_host = os.getenv("MYSQL_PROJECT_DB_HOST")
project_usr = os.getenv("MYSQL_PROJECT_DB_USER")
project_passw = os.getenv("MYSQL_PROJECT_DB_PASSWORD")
project_db = os.getenv("MYSQL_PROJECT_DB_NAME")

mqtt_topic = os.getenv("MQTT_TOPIC")
mqtt_broker = os.getenv("MQTT_BROKER")
mqtt_port = int(os.getenv("MQTT_PORT"))
mqtt_secure = bool(os.getenv("MQTT_SECURE"))
mqtt_user = os.getenv("MQTT_USER")
mqtt_password = os.getenv("MQTT_PASSWORD")

db_conn = None
db_cursor = None


def connect_to_database(host, usr, passw, db):
    try:
        internal_db_conn = mysql.connector.connect(
            host=host, user=usr, password=passw, database=db
        )
        internal_db_cursor = internal_db_conn.cursor()
        return internal_db_conn, internal_db_cursor
    except Exception as err:
        print("Erro ao conectar ao banco de dados:", err)
        return None, None


def get_project_db_data(internal_db_conn, internal_db_cursor, project):
    internal_db_cursor.execute(
        "SELECT host, user, password, `database` FROM projects WHERE origin = %s",
        (project,),
    )
    project_data = internal_db_cursor.fetchone()

    if project_data is None:
        print("Projeto não encontrado.")
        print("Utilizando o banco de dados padrão.")
        return project_host, project_usr, project_passw, project_db

    return (project_data[0], project_data[1], project_data[2], project_data[3])


def process_data(data):
    gateway_uuid = None
    gateway_name = None

    sensor_uuid = None
    sensor_data = None

    message = None

    project = project_db

    data_hora_formatada = None

    devices = []

    try:
        data_type = data.get("type", None)

        if data_type == "publication":
            sensor_uuid = data.get("uuid")
            raw_data = data.get("data")

            project = data.get("project", project_db)

            gateway_uuid = data.get("gateway").get("uuid")

            sensor_data = round(float(raw_data), 2) if raw_data is not None else None

            data_datetime = data.get("gathered_at").split("T")
            time_datetime = data_datetime[1].split(".")
            data_hora_formatada = data_datetime[0] + " " + time_datetime[0]

        elif data_type == "identification":
            gateway_uuid = data.get("gateway").get("uuid")
            gateway_name = data.get("gateway").get("name")

            devices = data.get("devices")

            data_datetime = data.get("gathered_at").split("T")
            time_datetime = data_datetime[1].split(".")
            data_hora_formatada = data_datetime[0] + " " + time_datetime[0]

        elif data_type == "log":
            gateway_uuid = data.get("gateway").get("uuid")
            message = data.get("data")

            data_datetime = data.get("gathered_at").split("T")
            time_datetime = data_datetime[1].split(".")
            data_hora_formatada = data_datetime[0] + " " + time_datetime[0]

        created_at = datetime.datetime.now()

        return {
            "project": project,
            "type": data_type,
            "gateway": {
                "uuid": gateway_uuid,
                "name": gateway_name,
            },
            "devices": devices,
            "sensor_data": {
                "uuid": sensor_uuid,
                "data": sensor_data,
                "date_time": data_hora_formatada,
            },
            "log": {
                "message": message,
                "date_time": data_hora_formatada,
            },
            "created_at": created_at,
        }
    except Exception as err:
        print("Erro ao processar os dados:", err)
        return None


def create_enviroment(data):
    global db_conn, db_cursor
    project = data.get("project") if data.get("project") else project_db
    db_cursor.execute("SELECT id FROM environments WHERE project = %s", (project,))
    environment_result = db_cursor.fetchone()

    if environment_result is None:
        # Ambiente não existe, insere novo ambiente
        environment_name = "temporary_name_" + project

        db_cursor.execute(
            "INSERT INTO environments (project, name) " "VALUES (%s, %s)",
            (
                project,
                environment_name,
            ),
        )
        environment_id = db_cursor.lastrowid
        db_conn.commit()
    else:
        environment_id = environment_result[0]

    return environment_id


def create_gateway(data):
    global db_conn, db_cursor

    # Verifica se o ambiente existe
    environment_id = create_enviroment(data)

    gateway_uuid = data.get("gateway").get("uuid")
    db_cursor.execute("SELECT id FROM gateways WHERE id = %s", (gateway_uuid,))
    gateway_result = db_cursor.fetchone()
    created_at = data.get("created_at")

    if gateway_result is None:
        # Gateway não existe, insere novo gateway
        gatweay = data.get("gateway").get("name")

        gateway_name = gatweay if gatweay else "temporary_name_" + gateway_uuid

        db_cursor.execute(
            "INSERT INTO gateways (id, environment_id, name, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                gateway_uuid,
                environment_id,
                gateway_name,
                created_at,
                created_at,
            ),
        )
        db_conn.commit()


# Processa os dados de publicação para disparar os scripts de regras
def process_pub_data(sensor_uuid, project):
    global db_cursor
    db_cursor.execute("SELECT path FROM scripts WHERE sensor_id = %s", (sensor_uuid,))
    sensor_scripts = db_cursor.fetchall()

    for sensor_script in sensor_scripts:
        script_path = sensor_script[0]
        subprocess.Popen(
            [
                "python3",
                os.path.join(script_dir, "scripts", script_path),
                str(sensor_uuid),
                project,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


# Insere os dados de publicação no banco de dados
def insert_pub_data(data):
    global db_conn, db_cursor
    # Verifica se o gateway existe
    create_gateway(data)
    # Verifica se o sensor existe
    sensor_uuid = data.get("sensor_data").get("uuid")
    db_cursor.execute("SELECT id FROM sensors WHERE id = %s", (sensor_uuid,))
    sensor_result = db_cursor.fetchone()
    created_at = data.get("created_at")

    if sensor_result is None:
        # Sensor não existe, insere novo sensor
        sensor_name = "temporary_name_" + sensor_uuid
        gateway_uuid = data.get("gateway").get("uuid")
        db_cursor.execute(
            "INSERT INTO sensors "
            "(id, name, gateway_id, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s)",
            (sensor_uuid, gateway_uuid, sensor_name, created_at, created_at),
        )

        db_conn.commit()

    value = data.get("sensor_data").get("data")
    value_date = data.get("sensor_data").get("date_time")

    # Insere os dados do sensor
    db_cursor.execute(
        "INSERT INTO sensor_data (sensor_id, data, gathered_at, created_at) "
        "VALUES (%s, %s, %s, %s)",
        (sensor_uuid, value, value_date, created_at),
    )
    db_conn.commit()


def insert_config_data(data):
    global db_conn, db_cursor
    # Verifica se o gateway existe
    create_gateway(data)

    # Verifica se cada sensor existe
    for sensor in data["devices"]:
        sensor_uuid = sensor.get("uuid")

        db_cursor.execute("SELECT id FROM sensors WHERE id = %s", (sensor_uuid,))
        sensor_result = db_cursor.fetchone()

        sensor_name = sensor.get("name")
        sensor_type = sensor.get("driver")
        created_at = data.get("created_at")

        sensor_types = {
            "temperature": 1,
            "humidity": 2,
            "conductivity": 3,
            "ph": 4,
            "pressure": 5,
            "wind": 6,
        }

        type_id = sensor_types.get(sensor_type, None)

        if sensor_result is None and type_id is not None:
            # Sensor não existe, insere novo sensor

            db_cursor.execute(
                "INSERT INTO sensors "
                "(id, gateway_id, type_id, name, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    sensor_uuid,
                    gateway_uuid,
                    type_id,
                    sensor_name,
                    created_at,
                    created_at,
                ),
            )

            db_conn.commit()
        elif type_id is not None:
            # Sensor existe, atualiza os seus dados
            db_cursor.execute(
                "UPDATE sensors SET "
                "gateway_id = %s, "
                "type_id = %s, "
                "name = %s, "
                "created_at = %s, "
                "updated_at = %s "
                "WHERE id = %s",
                (
                    gateway_uuid,
                    type_id,
                    sensor_name,
                    created_at,
                    created_at,
                    sensor_uuid,
                ),
            )

            db_conn.commit()


def insert_log_data(data):
    global db_conn, db_cursor
    # Verifica se o gateway existe
    create_gateway(data)

    message = data.get("log").get("message")
    value_date = data.get("log").get("date_time")
    gateway_uuid = data.get("gateway").get("uuid")

    # Insere os dados do log
    db_cursor.execute(
        "INSERT INTO logs (gateway_id, message, created_at) " "VALUES (%s, %s, %s)",
        (gateway_uuid, message, value_date),
    )
    db_conn.commit()


def insert_data_into_database(data):
    global db_conn, db_cursor
    if data is None:
        return
    try:
        internal_db_conn, internal_db_cursor = connect_to_database(
            internal_host, internal_usr, internal_passw, internal_db
        )

        project = data.get("project", project_db)

        host, usr, passw, db = get_project_db_data(
            internal_db_conn, internal_db_cursor, project
        )

        db_conn, db_cursor = connect_to_database(host, usr, passw, db)

        data_type = data.get("type")

        if data_type == "identification":
            insert_config_data(data)

        elif data_type == "publication":
            insert_pub_data(data)
            sensor_uuid = data.get("sensor_data").get("uuid")
            process_pub_data(sensor_uuid, project)

        elif data_type == "log":
            insert_log_data(data)

    except Exception as err:
        print("Erro ao inserir os dados no banco de dados:", err)

    finally:
        db_cursor.close()
        db_conn.close()


def on_connect(client, userdata, flags, rc):
    print("Conectado, com o seguinte retorno do Broker: " + str(rc))
    client.subscribe(mqtt_topic)


def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))
    try:
        m_decode = str(msg.payload.decode("utf-8", "ignore"))
        data = json.loads(m_decode)
        processed_data = process_data(data)
        if processed_data:
            insert_data_into_database(processed_data)
    except Exception as err:
        print("Erro ao receber ou processar a mensagem MQTT:", err)

    # try:
    #     subprocess.check_call(["python3", os.path.join(script_dir, "weather.py")])
    # except subprocess.CalledProcessError as e:
    #     print("Weather data collect failed.")
    #     print(e)


# client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message


if mqtt_secure:
    client.username_pw_set(mqtt_user, password=mqtt_password)

client.connect(mqtt_broker, mqtt_port)

client.loop_forever()
