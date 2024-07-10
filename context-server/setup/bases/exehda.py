import mysql.connector
import os
import sys
from dotenv import load_dotenv

load_dotenv()

if len(sys.argv) != 6:
    print(
        "exehda.py incorrect params. Expected: <PROJECT_NAME> <MYSQL_HOST> <MYSQL_USER> <MYSQL_PASSWORD> <MYSQL_DB_NAME>",
        "Received: ",
        sys.argv,
    )
    sys.exit(1)

project_name = sys.argv[1]

host = sys.argv[2]
usr = sys.argv[3]
passw = sys.argv[4]
db = sys.argv[5]

mydb = mysql.connector.connect(host=host, user=usr, password=passw)
cursor = mydb.cursor()

cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db}")

project_conn = mysql.connector.connect(host=host, user=usr, password=passw, database=db)
project_cursor = project_conn.cursor()

# Create the 'environments' table
project_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS environments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        data JSON,
        project VARCHAR(255),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
"""
)

# Create the 'gateways' table
project_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS gateways (
        id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
        environment_id INT,
        name VARCHAR(255),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (environment_id) REFERENCES environments (id) ON DELETE CASCADE
    )
"""
)

# Create the 'sensor_types' table
project_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS sensor_types (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        description TEXT,
        unit VARCHAR(50),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
"""
)

# Create the 'sensors' table
project_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS sensors (
        id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
        gateway_id VARCHAR(36),
        type_id INT,
        name VARCHAR(255),
        description TEXT,
        call_rule BOOLEAN DEFAULT True,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (gateway_id) REFERENCES gateways (id) ON DELETE CASCADE,
        FOREIGN KEY (type_id) REFERENCES sensor_types (id) ON DELETE SET NULL
    )
"""
)

# Create the 'sensor_data' table
project_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sensor_id VARCHAR(36),
        data FLOAT,
        gathered_at TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sensor_id) REFERENCES sensors (id) ON DELETE CASCADE
    )
"""
)

# Create the 'rules' table
project_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS rules (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sensor_id VARCHAR(36),
        type_id INT,
        ´condition´ TINYTEXT,
        value VARCHAR(12),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (sensor_id) REFERENCES sensors (id) ON DELETE CASCADE,
        FOREIGN KEY (type_id) REFERENCES sensor_types (id) ON DELETE CASCADE
    )
"""
)

# Create the 'logs' table
project_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        gateway_id VARCHAR(36),
        message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (gateway_id) REFERENCES gateways (id) ON DELETE CASCADE
    )
"""
)

# Create the 'scripts' table
project_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS scripts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sensor_id VARCHAR(36),
        name VARCHAR(64),
        description TEXT,
        path VARCHAR(128),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sensor_id) REFERENCES sensors (id) ON DELETE CASCADE
    )
"""
)

# Create the 'alerts' table
project_cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS alerts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sensor_id VARCHAR(36),
        script_id INT,
        is_sent BOOLEAN DEFAULT False,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sensor_id) REFERENCES sensors (id) ON DELETE CASCADE,
        FOREIGN KEY (script_id) REFERENCES scripts (id) ON DELETE CASCADE
    )
"""
)

project_conn.commit()
project_conn.close()
