# ########################################
# Gateway EXEHDA - iSim Version
# Authors: Graciela Viana
#          Ícaro Siqueira
#          Adenauer Yamin
#          Lizandro Oliveira
# Last editing: 2024-09-19 - 19:44 h
# ########################################

import subprocess
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

# Check dependencies
print("Checking dependencies...")
try:
    subprocess.check_call(
        ["python3", os.path.join(script_dir, "setup/dependencies-check.py")]
    )
except subprocess.CalledProcessError as e:
    print("Dependency check failed. Aborting.")
    print(e)
    exit(1)

# Migrate database
print("Running internal migrations...")
try:
    subprocess.check_call(["python3", os.path.join(script_dir, "setup/migrate.py")])
except subprocess.CalledProcessError as e:
    print("Internal migration failed. Aborting.")
    print(e)
    exit(1)

# Seed data
print("Seeding internal data...")
try:
    subprocess.check_call(["python3", os.path.join(script_dir, "setup/seed.py")])
except subprocess.CalledProcessError as e:
    print("Internal data seeding failed. Aborting.")
    print(e)
    exit(1)

# Migrate projects databases
print("Create projects databases...")
try:
    subprocess.check_call(["python3", os.path.join(script_dir, "setup/bases/index.py")])
except subprocess.CalledProcessError as e:
    print("Projects migration failed. Aborting.")
    print(e)
    exit(1)

print("All scripts executed successfully!")
