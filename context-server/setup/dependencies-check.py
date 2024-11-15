# ########################################
# Gateway EXEHDA - iSim Version
# Authors: Graciela Viana
#          Ícaro Siqueira
#          Adenauer Yamin
#          Lizandro Oliveira
# Last editing: 2024-09-19 - 19:44 h
# ########################################
import pkg_resources
import subprocess

# Define the required dependencies
dependencies = ["paho-mqtt", "datetime", "mysql-connector-python", "python-dotenv", "decorator"]

# Check if all dependencies are installed
missing_dependencies = []
for dependency in dependencies:
    try:
        pkg_resources.get_distribution(dependency)
    except pkg_resources.DistributionNotFound:
        missing_dependencies.append(dependency)

# Install missing dependencies
if missing_dependencies:
    print("The following dependencies are missing:")
    for dependency in missing_dependencies:
        print(dependency)
        try:
            subprocess.check_call(["pip3", "install", dependency])
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {dependency}. Error: {e}")
else:
    print("All dependencies are installed.")
