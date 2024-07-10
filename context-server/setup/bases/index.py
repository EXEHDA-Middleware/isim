import mysql.connector
import os
import sys
from dotenv import load_dotenv
import subprocess

# Get the directory of the current script (index.py)
script_dir = os.path.dirname(os.path.abspath(__file__))


if len(sys.argv) != 6:
    print(
        "To add new project databases use: python3 context-server/setup/bases/index.py <PROJECT_NAME> <MYSQL_HOST> <MYSQL_USER> <MYSQL_PASSWORD> <MYSQL_DB_NAME>"
    )

load_dotenv()

host = os.getenv("MYSQL_INTERNAL_DB_HOST")
usr = os.getenv("MYSQL_INTERNAL_DB_USER")
passw = os.getenv("MYSQL_INTERNAL_DB_PASSWORD")
db = os.getenv("MYSQL_INTERNAL_DB_NAME")

i2mf_conn = mysql.connector.connect(host=host, user=usr, password=passw, database=db)
i2mf_cursor = i2mf_conn.cursor()

# Insert project data into projects table is params are passed
if len(sys.argv) == 6:
    # Get project data params from command line
    project_name = sys.argv[1]
    project_host = sys.argv[2]
    project_usr = sys.argv[3]
    project_passw = sys.argv[4]
    project_db = sys.argv[5]

    sql = "INSERT INTO projects (origin, host, user, password, `database`) VALUES (%s, %s, %s, %s, %s)"
    try:
        i2mf_cursor.execute(
            sql, (project_name, project_host, project_usr, project_passw, project_db)
        )
        i2mf_conn.commit()
        print(f"Project '{project_name}' created successfully.")
    except mysql.connector.errors.IntegrityError as e:
        print(f"Failed to create project '{project_name}': {e}")

# Check if projects table already has data
i2mf_cursor.execute("SELECT * FROM projects")
projects = i2mf_cursor.fetchall()

# Loop calls to exehda.py script passing the columns as params
for project in projects:
    print("Create projects databases...")
    try:
        subprocess.check_call(
            [
                "python3",
                os.path.join(script_dir, "exehda.py"),
                project[1],
                project[2],
                project[3],
                project[4],
                project[5],
            ]
        )
    except subprocess.CalledProcessError as e:
        print("Projects migration failed. Aborting.")
        print(e)
        exit(1)

    # Seed data
    print("Seeding project databases...")
    try:
        subprocess.check_call(
            [
                "python3",
                os.path.join(script_dir, "seed.py"),
                project[1],
                project[2],
                project[3],
                project[4],
                project[5],
            ]
        )
    except subprocess.CalledProcessError as e:
        print("Projects data seeding failed. Aborting.")
        print(e)
        exit(1)

i2mf_conn.close()
