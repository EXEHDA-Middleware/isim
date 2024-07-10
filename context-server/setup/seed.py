import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("MYSQL_INTERNAL_DB_HOST")
usr = os.getenv("MYSQL_INTERNAL_DB_USER")
passw = os.getenv("MYSQL_INTERNAL_DB_PASSWORD")
db = os.getenv("MYSQL_INTERNAL_DB_NAME")

project_host = os.getenv("MYSQL_PROJECT_DB_HOST")
project_usr = os.getenv("MYSQL_PROJECT_DB_USER")
project_passw = os.getenv("MYSQL_PROJECT_DB_PASSWORD")
project_db = os.getenv("MYSQL_PROJECT_DB_NAME")

i2mf_conn = mysql.connector.connect(host=host, user=usr, password=passw, database=db)
i2mf_cursor = i2mf_conn.cursor()

# Check if projects table already has data
i2mf_cursor.execute("SELECT COUNT(*) FROM projects")
result = i2mf_cursor.fetchone()

if result[0] > 0:
    print("Projects already registered in the table. Skipping seeding.")
else:
    sql = "INSERT INTO projects (origin, host, user, password, `database`) VALUES (%s, %s, %s, %s, %s)"
    i2mf_cursor.execute(
        sql, (project_db, project_host, project_usr, project_passw, project_db)
    )
    i2mf_conn.commit()

print("Projects seeding data completed.")
i2mf_conn.close()
