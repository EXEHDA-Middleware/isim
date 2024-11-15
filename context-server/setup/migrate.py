# ########################################
# Gateway EXEHDA - iSim Version
# Authors: Graciela Viana
#          Ícaro Siqueira
#          Adenauer Yamin
#          Lizandro Oliveira
# Last editing: 2024-09-19 - 19:44 h
# ########################################
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("MYSQL_INTERNAL_DB_HOST")
usr = os.getenv("MYSQL_INTERNAL_DB_USER")
passw = os.getenv("MYSQL_INTERNAL_DB_PASSWORD")

db = os.getenv("MYSQL_INTERNAL_DB_NAME")

mydb = mysql.connector.connect(host=host, user=usr, password=passw)
i2mf_cursor = mydb.cursor()

i2mf_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db}")

i2mf_conn = mysql.connector.connect(host=host, user=usr, password=passw, database=db)
i2mf_cursor = i2mf_conn.cursor()

# Create the 'projects' table
i2mf_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS projects (
        id INT AUTO_INCREMENT PRIMARY KEY,
        origin VARCHAR(255) UNIQUE,
        host VARCHAR(255),
        user VARCHAR(255),
        password VARCHAR(255),
        `database` VARCHAR(255),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
"""
)

# Create the 'logs' table
i2mf_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        project_id INT,
        message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    )
"""
)

# Create the 'telegram_users' table
i2mf_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS telegram_users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        project_id INT,
        code VARCHAR(16),
        active BOOLEAN DEFAULT True,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    )
"""
)

i2mf_conn.commit()
i2mf_conn.close()
