import mysql.connector
import sys

if len(sys.argv) != 6:
    print(
        "seed.py incorrect params. Expected: <PROJECT_NAME> <MYSQL_HOST> <MYSQL_USER> <MYSQL_PASSWORD> <MYSQL_DB_NAME>",
        "Received: ",
        sys.argv,
    )
    sys.exit(1)

project = sys.argv[1]

host = sys.argv[2]
usr = sys.argv[3]
passw = sys.argv[4]
db = sys.argv[5]

db_conn = mysql.connector.connect(host=host, user=usr, password=passw, database=db)
db_cursor = db_conn.cursor()

# Check if sensor_types table already has data
db_cursor.execute("SELECT COUNT(*) FROM sensor_types")
result = db_cursor.fetchone()

if result[0] > 0:
    print(
        f"Sensor types from {project} project already exist in the table. Skipping seeding."
    )
else:
    # Sensor type data
    sensor_types = [
        ("temperature", "Temperature", "°C"),
        ("humidity", "Air Humidity", "%"),
        ("conductivity", "Electric Conductivity", "uS/cm"),
        ("ph", "Water pH", "ph"),
        ("pressure", "Water Level", "m3"),
        ("wind", "Wind Velocity", "km/h"),
    ]

    # Add sensor types to the table
    for sensor_type in sensor_types:
        sql = "INSERT INTO sensor_types (name, description, unit) VALUES (%s, %s, %s)"
        db_cursor.execute(sql, sensor_type)

    db_conn.commit()

# db_cursor.execute("SELECT COUNT(*) FROM environments")
# result = db_cursor.fetchone()

# if result[0] > 0:
#     print(
#         f"Environments from {project} project already exist in the table. Skipping seeding."
#     )
# else:
#     # Environments names
#     environments_names = [f"Reservatório R{i}" for i in range(1, 25)]

#     # Add environments to the table
#     for environment_name in environments_names:
#         sql = "INSERT INTO environments (name) VALUES (%s)"
#         db_cursor.execute(sql, (environment_name,))

#     db_conn.commit()

print(f"Seeding {project} project data completed.")
db_conn.close()
