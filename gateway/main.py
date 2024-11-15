# ########################################
# Gateway EXEHDA - iSim Version
# Authors: Graciela Viana
#          Ícaro Siqueira
#          Adenauer Yamin
#          Lizandro Oliveira
# Last editing: 2024-09-19 - 19:44 h
# ########################################
import onewire, ds18x20
import sys

global pinn
import _thread
from umqtt.simple import MQTTClient
import ujson
import time
import ntptime
import utime
from machine import Pin, Timer, SoftI2C, RTC, WDT
from ds3231_port import DS3231
import machine
import os
import ubinascii
import time, machine
import aht

print("Program main.py started")

# Physical Associations
red = machine.Pin(25, machine.Pin.OUT)
yellow = machine.Pin(33, machine.Pin.OUT)
green = machine.Pin(32, machine.Pin.OUT)
buzzer = machine.Pin(26, machine.Pin.OUT)
I2C_RTC_SCL_PIN = Pin(22)
I2C_RTC_SDA_PIN = Pin(21)

# Buzzer Ativation to Register the Gateway Operations Start
buzzer.value(1)
time.sleep(0.5)
buzzer.value(0)

# WatchDog ativation - 20 minutes
wdtimer = WDT(timeout=1200000)

# Variables of Type List to Register Sensors Values
publication_payload = []
publication_topic = []

# MQTT Settings
mqtt_client_id = ubinascii.hexlify(machine.unique_id())
mqtt_server = "200.132.103.53"

# I2C Settings
# I2C Clock Settings
i2c_clock = SoftI2C(scl=I2C_RTC_SCL_PIN, sda=I2C_RTC_SDA_PIN)
rtc_ds3231 = DS3231(i2c_clock)

# AHT25 Settings:
i2c_aht25 = machine.SoftI2C(scl=machine.Pin(22), sda=machine.Pin(21))
aht25_sensor = aht.AHT2x(i2c_aht25, crc=True)

# DS18b20 first read error handling
gpio_port = 13
temperature_sensor_pin = Pin(gpio_port)
ds = ds18x20.DS18X20(onewire.OneWire(temperature_sensor_pin))
temperature_sensor_list = ds.scan()
ds.convert_temp()
sensor_value1 = ds.read_temp(temperature_sensor_list[0])
sensor_value2 = ds.read_temp(temperature_sensor_list[1])


# Function that places the data to be transmitted in the last position of the queue
def stack_pub(mqtt_type, uuid_sensor, mqtt_topic, payload):

    global publication_payload
    global publication_topic

    ano = time.localtime()[0]
    mes = time.localtime()[1]
    dia = time.localtime()[2]
    hora = time.localtime()[3]
    minuto = time.localtime()[4]
    segundo = time.localtime()[5]

    datahorautc = (
        str(ano)
        + "-"
        + str(mes)
        + "-"
        + str(dia)
        + "T"
        + str(hora)
        + ":"
        + str(minuto)
        + "."
        + str(segundo)
    )

    dict = {}
    dict["gathered_at"] = datahorautc
    dict["type"] = mqtt_type
    if uuid_sensor != "":
        dict["uuid"] = uuid_sensor
    dict["gateway"] = {}
    dict["gateway"]["uuid"] = "15014c0c-694d-45ee-8190-f924a8573947"
    dict["data"] = payload

    mqtt_payload = ujson.dumps(dict)

    publication_topic.append(mqtt_topic)
    publication_payload.append(mqtt_payload)


# Function that transmits data using the oldest first criteria as a criterion
def mqtt_publication():
    global publication_payload
    global publication_topic
    mqtt_pub_tentatives = 0
    try:
        client_g = MQTTClient(
            mqtt_client_id, mqtt_server, user="middleware", password="exehda"
        )
        client_g.connect()
        green.value(1)
        while len(publication_topic) > 0:
            try:
                client_g.publish(publication_topic[0], publication_payload[0].encode())
                publication_topic.pop(0)
                publication_payload.pop(0)
                time.sleep(1)
            except:
                mqtt_pub_tentatives = mqtt_pub_tentatives + 1
                print("MQTT Publication tentatives: %s" % str(mqtt_pub_tentatives))
                time.sleep(2)
                if mqtt_pub_tentatives > 3:
                    break
        client_g.disconnect()
        green.value(0)
    except:
        stack_pub("log", "", "exehda-pub", "Unable to connect MQTT Broker")


def conecta_rede():
    import network

    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        sta_if.active(True)
        sta_if.connect("iSim-Net", "exehda@#")
        #        sta_if.connect('EXEHDA_2G', '!luz@azul#')
        #        sta_if.connect('EXEHDA-0', 'acy12345')
        red.value(1)
        while not sta_if.isconnected():
            pass  # wait till connection
    red.value(0)


_thread.start_new_thread(conecta_rede, ())


# Time interval to cancel the execution - 15 seconds
yellow.value(1)
print("Time interval to cancel the execution started - 15 seconds")
time.sleep(15)
yellow.value(0)
print("Time interval to cancel the execution finished - 15 seconds")

# NTP to internal clock adjust
tentativas_ajuste_relogio = 0
ajuste_relogio = 0
while ajuste_relogio == 0 and tentativas_ajuste_relogio <= 10:
    print(ajuste_relogio)
    try:
        ntptime.host = "a.ntp.br"
        ntptime.settime()
        ajuste_relogio = 1
    except:
        time.sleep(5)
        tentativas_ajuste_relogio = tentativas_ajuste_relogio + 1
        print("Tentativas ajuste relogio：%s" % str(tentativas_ajuste_relogio))
        ajuste_relogio = 0

if ajuste_relogio == 1:
    rtc_ds3231.save_time()
    started_time_source = "Gateway restarted with NTP time atualization"
else:
    tm = rtc_ds3231.get_time()
    RTC().datetime((tm[0], tm[1], tm[2], tm[6], tm[3], tm[4], tm[5], 0))
    started_time_source = (
        "Gateway restarted with time atualized from local clock (DS3231)"
    )

stack_pub("log", "", "exehda-pub", started_time_source)

DS3231_time = "DS3231 time at restart: " + str(rtc_ds3231.get_time())
stack_pub("log", "", "exehda-pub", DS3231_time)

try:
    file_sensor_topic = open("sensor_topic.txt", "r")
    lista_publication_topic = file_sensor_topic.read()
    data_publication_topic = lista_publication_topic.split("\n")
    while len(data_publication_topic) > 0:
        if len(data_publication_topic[0]) > 0:
            publication_topic.append(data_publication_topic[0])
        data_publication_topic.pop(0)
    file_sensor_topic.close()
    os.remove("sensor_topic.txt")
#    print("Gateway restarted with recovery topic sensor data file")
except:
    print("Gateway restarted without recovery topic sensor data file")

try:
    file_sensor_payload = open("sensor_payload.txt", "r")
    lista_publication_payload = file_sensor_payload.read()
    data_publication_payload = lista_publication_payload.split("\n")
    while len(data_publication_payload) > 0:
        if len(data_publication_payload[0]) > 0:
            publication_payload.append(data_publication_payload[0])
        data_publication_payload.pop(0)
    file_sensor_payload.close()
    os.remove("sensor_payload.txt")
    #    print("Gateway restarted with recovery payload sensor data file")
    recovery_status = "Gateway restarted with recovery from sensor data file"
except:
    #    print("Gateway restarted without recovery payload sensor data file")
    recovery_status = "Gateway restarted without recovery from sensor data file"

stack_pub("log", "", "exehda-pub", recovery_status)


mqtt_publication()


def sensor_read_simulated():

    valor_umidade_ar = 00.00
    condutividade_agua = 00.00
    ph_agua = 0.00
    pressao_reservatorio = 00.00
    hora = time.localtime()[3]
    minuto = time.localtime()[4]

    if hora == 3:
        if minuto == 0:
            valor_umidade_ar = 93
            condutividade_agua = 61.86
            ph_agua = 6.97
            pressao_reservatorio = 10.67

        if minuto == 10:
            valor_umidade_ar = 93
            condutividade_agua = 60.63
            ph_agua = 6.83
            pressao_reservatorio = 10.88

        if minuto == 20:
            valor_umidade_ar = 93
            condutividade_agua = 59.08
            ph_agua = 6.65
            pressao_reservatorio = 11.09

        if minuto == 30:
            valor_umidade_ar = 94
            condutividade_agua = 56.92
            ph_agua = 6.41
            pressao_reservatorio = 11.3

        if minuto == 40:
            valor_umidade_ar = 94
            condutividade_agua = 56.3
            ph_agua = 6.34
            pressao_reservatorio = 11.51

        if minuto == 50:
            valor_umidade_ar = 95
            condutividade_agua = 55.99
            ph_agua = 6.3
            pressao_reservatorio = 11.72

    if hora == 4:
        if minuto == 0:
            valor_umidade_ar = 95
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 11.7

        if minuto == 10:
            valor_umidade_ar = 95
            condutividade_agua = 55.37
            ph_agua = 6.23
            pressao_reservatorio = 11.92

        if minuto == 20:
            valor_umidade_ar = 95
            condutividade_agua = 55.06
            ph_agua = 6.2
            pressao_reservatorio = 12.14

        if minuto == 30:
            valor_umidade_ar = 95
            condutividade_agua = 55.06
            ph_agua = 6.2
            pressao_reservatorio = 12.36

        if minuto == 40:
            valor_umidade_ar = 96
            condutividade_agua = 53.82
            ph_agua = 6.06
            pressao_reservatorio = 12.58

        if minuto == 50:
            valor_umidade_ar = 96
            condutividade_agua = 52.89
            ph_agua = 5.96
            pressao_reservatorio = 12.8

    if hora == 5:
        if minuto == 0:
            valor_umidade_ar = 96
            condutividade_agua = 52.58
            ph_agua = 5.92
            pressao_reservatorio = 12.81

        if minuto == 10:
            valor_umidade_ar = 96
            condutividade_agua = 53.2
            ph_agua = 5.92
            pressao_reservatorio = 13

        if minuto == 20:
            valor_umidade_ar = 95
            condutividade_agua = 54.13
            ph_agua = 6.1
            pressao_reservatorio = 13.19

        if minuto == 30:
            valor_umidade_ar = 95
            condutividade_agua = 54.75
            ph_agua = 6.17
            pressao_reservatorio = 13.38

        if minuto == 40:
            valor_umidade_ar = 95
            condutividade_agua = 55.37
            ph_agua = 6.23
            pressao_reservatorio = 13.57

        if minuto == 50:
            valor_umidade_ar = 94
            condutividade_agua = 55.37
            ph_agua = 6.23
            pressao_reservatorio = 13.76

    if hora == 6:
        if minuto == 0:
            valor_umidade_ar = 94
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 13.78

        if minuto == 10:
            valor_umidade_ar = 94
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 13.98

        if minuto == 20:
            valor_umidade_ar = 94
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 14.18

        if minuto == 30:
            valor_umidade_ar = 94
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 14.38

        if minuto == 40:
            valor_umidade_ar = 94
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 14.58

        if minuto == 50:
            valor_umidade_ar = 94
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 14.78

    if hora == 7:
        if minuto == 0:
            valor_umidade_ar = 93
            condutividade_agua = 55.38
            ph_agua = 6.27
            pressao_reservatorio = 14.8

        if minuto == 10:
            valor_umidade_ar = 93
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 15.02

        if minuto == 20:
            valor_umidade_ar = 93
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 15.24

        if minuto == 30:
            valor_umidade_ar = 93
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 15.46

        if minuto == 40:
            valor_umidade_ar = 93
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 15.68

        if minuto == 50:
            valor_umidade_ar = 93
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 15.9

    if hora == 8:
        if minuto == 0:
            valor_umidade_ar = 93
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 15.9

        if minuto == 10:
            valor_umidade_ar = 93
            condutividade_agua = 55.24
            ph_agua = 6.22
            pressao_reservatorio = 16.12

        if minuto == 20:
            valor_umidade_ar = 93
            condutividade_agua = 54.81
            ph_agua = 6.17
            pressao_reservatorio = 16.34

        if minuto == 30:
            valor_umidade_ar = 93
            condutividade_agua = 54.38
            ph_agua = 6.12
            pressao_reservatorio = 16.56

        if minuto == 40:
            valor_umidade_ar = 94
            condutividade_agua = 53.95
            ph_agua = 6.07
            pressao_reservatorio = 16.78

        if minuto == 50:
            valor_umidade_ar = 94
            condutividade_agua = 53.2
            ph_agua = 5.99
            pressao_reservatorio = 16.9

    if hora == 9:
        if minuto == 0:
            valor_umidade_ar = 94
            condutividade_agua = 52.58
            ph_agua = 5.92
            pressao_reservatorio = 17

        if minuto == 10:
            valor_umidade_ar = 94
            condutividade_agua = 51.97
            ph_agua = 5.85
            pressao_reservatorio = 16.96

        if minuto == 20:
            valor_umidade_ar = 94
            condutividade_agua = 51.04
            ph_agua = 5.75
            pressao_reservatorio = 16.92

        if minuto == 30:
            valor_umidade_ar = 94
            condutividade_agua = 51.04
            ph_agua = 5.75
            pressao_reservatorio = 16.88

        if minuto == 40:
            valor_umidade_ar = 93
            condutividade_agua = 50.42
            ph_agua = 5.68
            pressao_reservatorio = 16.84

        if minuto == 50:
            valor_umidade_ar = 93
            condutividade_agua = 49.8
            ph_agua = 5.61
            pressao_reservatorio = 16.82

    if hora == 10:
        if minuto == 0:
            valor_umidade_ar = 93
            condutividade_agua = 49.49
            ph_agua = 5.57
            pressao_reservatorio = 16.8

        if minuto == 10:
            valor_umidade_ar = 93
            condutividade_agua = 49.49
            ph_agua = 5.57
            pressao_reservatorio = 16.74

        if minuto == 20:
            valor_umidade_ar = 93
            condutividade_agua = 49.49
            ph_agua = 5.57
            pressao_reservatorio = 16.68

        if minuto == 30:
            valor_umidade_ar = 92
            condutividade_agua = 49.49
            ph_agua = 5.57
            pressao_reservatorio = 16.62

        if minuto == 40:
            valor_umidade_ar = 92
            condutividade_agua = 49.49
            ph_agua = 5.57
            pressao_reservatorio = 16.56

        if minuto == 50:
            valor_umidade_ar = 91
            condutividade_agua = 49.49
            ph_agua = 5.57
            pressao_reservatorio = 16.52

    if hora == 11:
        if minuto == 0:
            valor_umidade_ar = 90
            condutividade_agua = 49.49
            ph_agua = 5.57
            pressao_reservatorio = 16.5

        if minuto == 10:
            valor_umidade_ar = 90
            condutividade_agua = 50.11
            ph_agua = 5.64
            pressao_reservatorio = 16.44

        if minuto == 20:
            valor_umidade_ar = 90
            condutividade_agua = 50.11
            ph_agua = 5.64
            pressao_reservatorio = 16.38

        if minuto == 30:
            valor_umidade_ar = 89
            condutividade_agua = 50.73
            ph_agua = 5.71
            pressao_reservatorio = 16.32

        if minuto == 40:
            valor_umidade_ar = 89
            condutividade_agua = 51.66
            ph_agua = 5.82
            pressao_reservatorio = 16.32

        if minuto == 50:
            valor_umidade_ar = 89
            condutividade_agua = 52.28
            ph_agua = 5.89
            pressao_reservatorio = 16.2

    if hora == 12:
        if minuto == 0:
            valor_umidade_ar = 88
            condutividade_agua = 52.58
            ph_agua = 5.92
            pressao_reservatorio = 16

        if minuto == 10:
            valor_umidade_ar = 88
            condutividade_agua = 52.58
            ph_agua = 5.92
            pressao_reservatorio = 15.9

        if minuto == 20:
            valor_umidade_ar = 88
            condutividade_agua = 52.58
            ph_agua = 5.92
            pressao_reservatorio = 15.8

        if minuto == 30:
            valor_umidade_ar = 87
            condutividade_agua = 52.58
            ph_agua = 5.92
            pressao_reservatorio = 15.7

        if minuto == 40:
            valor_umidade_ar = 86
            condutividade_agua = 52.58
            ph_agua = 5.92
            pressao_reservatorio = 15.6

        if minuto == 50:
            valor_umidade_ar = 86
            condutividade_agua = 52.58
            ph_agua = 5.92
            pressao_reservatorio = 15.5

    if hora == 13:
        if minuto == 0:
            valor_umidade_ar = 85
            condutividade_agua = 52.58
            ph_agua = 5.92
            pressao_reservatorio = 15.5

        if minuto == 10:
            valor_umidade_ar = 85
            condutividade_agua = 53.82
            ph_agua = 6.06
            pressao_reservatorio = 15.41

        if minuto == 20:
            valor_umidade_ar = 85
            condutividade_agua = 53.82
            ph_agua = 6.06
            pressao_reservatorio = 15.32

        if minuto == 30:
            valor_umidade_ar = 85
            condutividade_agua = 54.13
            ph_agua = 6.1
            pressao_reservatorio = 15.23

        if minuto == 40:
            valor_umidade_ar = 85
            condutividade_agua = 55.06
            ph_agua = 6.2
            pressao_reservatorio = 15.14

        if minuto == 50:
            valor_umidade_ar = 85
            condutividade_agua = 55.06
            ph_agua = 6.2
            pressao_reservatorio = 15.1

    if hora == 14:
        if minuto == 0:
            valor_umidade_ar = 85
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 15.05

        if minuto == 10:
            valor_umidade_ar = 83
            condutividade_agua = 56.61
            ph_agua = 6.37
            pressao_reservatorio = 14.96

        if minuto == 20:
            valor_umidade_ar = 83
            condutividade_agua = 56.61
            ph_agua = 6.37
            pressao_reservatorio = 14.87

        if minuto == 30:
            valor_umidade_ar = 81
            condutividade_agua = 57.53
            ph_agua = 6.48
            pressao_reservatorio = 14.78

        if minuto == 40:
            valor_umidade_ar = 81
            condutividade_agua = 57.53
            ph_agua = 6.48
            pressao_reservatorio = 14.69

        if minuto == 50:
            valor_umidade_ar = 80
            condutividade_agua = 58.46
            ph_agua = 6.58
            pressao_reservatorio = 14.6

    if hora == 15:
        if minuto == 0:
            valor_umidade_ar = 81
            condutividade_agua = 58.77
            ph_agua = 6.62
            pressao_reservatorio = 14.56

        if minuto == 10:
            valor_umidade_ar = 78
            condutividade_agua = 59.7
            ph_agua = 6.72
            pressao_reservatorio = 14.39

        if minuto == 20:
            valor_umidade_ar = 75
            condutividade_agua = 59.7
            ph_agua = 6.72
            pressao_reservatorio = 14.22

        if minuto == 30:
            valor_umidade_ar = 72
            condutividade_agua = 60.32
            ph_agua = 6.79
            pressao_reservatorio = 14.05

        if minuto == 40:
            valor_umidade_ar = 70
            condutividade_agua = 60.63
            ph_agua = 6.83
            pressao_reservatorio = 13.88

        if minuto == 50:
            valor_umidade_ar = 63
            condutividade_agua = 61.56
            ph_agua = 6.93
            pressao_reservatorio = 13.71

    if hora == 16:
        if minuto == 0:
            valor_umidade_ar = 65
            condutividade_agua = 61.86
            ph_agua = 6.97
            pressao_reservatorio = 13.7

        if minuto == 10:
            valor_umidade_ar = 63
            condutividade_agua = 61.86
            ph_agua = 6.97
            pressao_reservatorio = 13.57

        if minuto == 20:
            valor_umidade_ar = 61
            condutividade_agua = 62.79
            ph_agua = 7.07
            pressao_reservatorio = 13.44

        if minuto == 30:
            valor_umidade_ar = 59
            condutividade_agua = 63.1
            ph_agua = 7.11
            pressao_reservatorio = 13.31

        if minuto == 40:
            valor_umidade_ar = 57
            condutividade_agua = 64.03
            ph_agua = 7.21
            pressao_reservatorio = 13.18

        if minuto == 50:
            valor_umidade_ar = 56
            condutividade_agua = 64.34
            ph_agua = 7.24
            pressao_reservatorio = 13.05

    if hora == 17:
        if minuto == 0:
            valor_umidade_ar = 55
            condutividade_agua = 64.96
            ph_agua = 7.31
            pressao_reservatorio = 13.02

        if minuto == 10:
            valor_umidade_ar = 54
            condutividade_agua = 64.96
            ph_agua = 7.31
            pressao_reservatorio = 13

        if minuto == 20:
            valor_umidade_ar = 53
            condutividade_agua = 64.89
            ph_agua = 7.42
            pressao_reservatorio = 12.99

        if minuto == 30:
            valor_umidade_ar = 52
            condutividade_agua = 66.5
            ph_agua = 7.49
            pressao_reservatorio = 12.98

        if minuto == 40:
            valor_umidade_ar = 52
            condutividade_agua = 67.12
            ph_agua = 7.56
            pressao_reservatorio = 12.97

        if minuto == 50:
            valor_umidade_ar = 50
            condutividade_agua = 67.43
            ph_agua = 7.59
            pressao_reservatorio = 12.96

    if hora == 18:
        if minuto == 0:
            valor_umidade_ar = 51
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.94

        if minuto == 10:
            valor_umidade_ar = 51
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.9

        if minuto == 20:
            valor_umidade_ar = 50
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.86

        if minuto == 30:
            valor_umidade_ar = 50
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.82

        if minuto == 40:
            valor_umidade_ar = 49
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.78

        if minuto == 50:
            valor_umidade_ar = 48
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.74

    if hora == 19:
        if minuto == 0:
            valor_umidade_ar = 48
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.72

        if minuto == 10:
            valor_umidade_ar = 47
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.66

        if minuto == 20:
            valor_umidade_ar = 46
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.6

        if minuto == 30:
            valor_umidade_ar = 46
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.54

        if minuto == 40:
            valor_umidade_ar = 45
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.48

        if minuto == 50:
            valor_umidade_ar = 44
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.42

    if hora == 20:
        if minuto == 0:
            valor_umidade_ar = 44
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.4

        if minuto == 10:
            valor_umidade_ar = 44
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.36

        if minuto == 20:
            valor_umidade_ar = 44
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.32

        if minuto == 30:
            valor_umidade_ar = 44
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.28

        if minuto == 40:
            valor_umidade_ar = 44
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.24

        if minuto == 50:
            valor_umidade_ar = 44
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.22

    if hora == 21:
        if minuto == 0:
            valor_umidade_ar = 44
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.2

        if minuto == 10:
            valor_umidade_ar = 44
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.12

        if minuto == 20:
            valor_umidade_ar = 45
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 12.04

        if minuto == 30:
            valor_umidade_ar = 46
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 11.96

        if minuto == 40:
            valor_umidade_ar = 47
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 11.9

        if minuto == 50:
            valor_umidade_ar = 47
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 11.85

    if hora == 22:
        if minuto == 0:
            valor_umidade_ar = 48
            condutividade_agua = 68.05
            ph_agua = 7.66
            pressao_reservatorio = 11.8

        if minuto == 10:
            valor_umidade_ar = 49
            condutividade_agua = 67.74
            ph_agua = 7.63
            pressao_reservatorio = 11.74

        if minuto == 20:
            valor_umidade_ar = 50
            condutividade_agua = 67.12
            ph_agua = 7.56
            pressao_reservatorio = 11.68

        if minuto == 30:
            valor_umidade_ar = 51
            condutividade_agua = 66.5
            ph_agua = 7.49
            pressao_reservatorio = 11.62

        if minuto == 40:
            valor_umidade_ar = 52
            condutividade_agua = 65.89
            ph_agua = 7.42
            pressao_reservatorio = 11.56

        if minuto == 50:
            valor_umidade_ar = 53
            condutividade_agua = 65.27
            ph_agua = 7.35
            pressao_reservatorio = 11.53

    if hora == 23:
        if minuto == 0:
            valor_umidade_ar = 54
            condutividade_agua = 64.96
            ph_agua = 7.31
            pressao_reservatorio = 11.5

        if minuto == 10:
            valor_umidade_ar = 56
            condutividade_agua = 63.41
            ph_agua = 7.14
            pressao_reservatorio = 11.44

        if minuto == 20:
            valor_umidade_ar = 58
            condutividade_agua = 63.1
            ph_agua = 7.11
            pressao_reservatorio = 11.38

        if minuto == 30:
            valor_umidade_ar = 59
            condutividade_agua = 62.79
            ph_agua = 7.07
            pressao_reservatorio = 11.32

        if minuto == 40:
            valor_umidade_ar = 61
            condutividade_agua = 61.56
            ph_agua = 6.93
            pressao_reservatorio = 11.26

        if minuto == 50:
            valor_umidade_ar = 62
            condutividade_agua = 60.01
            ph_agua = 6.76
            pressao_reservatorio = 11.23

    if hora == 00:
        if minuto == 0:
            valor_umidade_ar = 63
            condutividade_agua = 58.77
            ph_agua = 6.62
            pressao_reservatorio = 11.2

        if minuto == 10:
            valor_umidade_ar = 65
            condutividade_agua = 57.53
            ph_agua = 6.48
            pressao_reservatorio = 11.12

        if minuto == 20:
            valor_umidade_ar = 67
            condutividade_agua = 57.22
            ph_agua = 6.44
            pressao_reservatorio = 11.04

        if minuto == 30:
            valor_umidade_ar = 69
            condutividade_agua = 55.68
            ph_agua = 6.27
            pressao_reservatorio = 10.96

        if minuto == 40:
            valor_umidade_ar = 71
            condutividade_agua = 54.13
            ph_agua = 6.1
            pressao_reservatorio = 10.88

        if minuto == 50:
            valor_umidade_ar = 74
            condutividade_agua = 53.51
            ph_agua = 6.03
            pressao_reservatorio = 10.8

    if hora == 1:
        if minuto == 0:
            valor_umidade_ar = 75
            condutividade_agua = 52.58
            ph_agua = 5.92
            pressao_reservatorio = 10.8

        if minuto == 10:
            valor_umidade_ar = 76
            condutividade_agua = 52.28
            ph_agua = 5.89
            pressao_reservatorio = 10.78

        if minuto == 20:
            valor_umidade_ar = 79
            condutividade_agua = 51.04
            ph_agua = 5.75
            pressao_reservatorio = 10.76

        if minuto == 30:
            valor_umidade_ar = 79
            condutividade_agua = 50.42
            ph_agua = 5.68
            pressao_reservatorio = 10.74

        if minuto == 40:
            valor_umidade_ar = 80
            condutividade_agua = 50.11
            ph_agua = 5.64
            pressao_reservatorio = 10.72

        if minuto == 50:
            valor_umidade_ar = 81
            condutividade_agua = 50.11
            ph_agua = 5.64
            pressao_reservatorio = 10.71

    if hora == 2:
        if minuto == 0:
            valor_umidade_ar = 82
            condutividade_agua = 49.49
            ph_agua = 5.57
            pressao_reservatorio = 10.7

        if minuto == 10:
            valor_umidade_ar = 85
            condutividade_agua = 52.58
            ph_agua = 5.92
            pressao_reservatorio = 10.69

        if minuto == 20:
            valor_umidade_ar = 87
            condutividade_agua = 54.13
            ph_agua = 6.1
            pressao_reservatorio = 10.69

        if minuto == 30:
            valor_umidade_ar = 90
            condutividade_agua = 56.3
            ph_agua = 6.34
            pressao_reservatorio = 10.68

        if minuto == 40:
            valor_umidade_ar = 91
            condutividade_agua = 58.77
            ph_agua = 6.62
            pressao_reservatorio = 10.68

        if minuto == 50:
            valor_umidade_ar = 92
            condutividade_agua = 60.63
            ph_agua = 6.83
            pressao_reservatorio = 10.68

    if aht25_sensor.is_ready:
        valor_umidade_aht25 = aht25_sensor.humidity
        valor_temperatura_aht25 = aht25_sensor.temperature
        stack_pub(
            "publication",
            "0c0a40d1-5a15-4f26-b85f-25868dfff6ee",
            "exehda-pub",
            valor_umidade_aht25,
        )
        stack_pub(
            "publication",
            "aaa6b88b-73fe-425f-9db9-ae3a27b2401f",
            "exehda-pub",
            valor_temperatura_aht25,
        )

    stack_pub(
        "publication",
        "c96e3b82-6e50-4b39-86d4-ab175dbdeb49",
        "exehda-pub",
        condutividade_agua,
    )

    stack_pub(
        "publication", "e038eaa2-15de-44e0-8395-d3299e69a5d0", "exehda-pub", ph_agua
    )

    stack_pub(
        "publication",
        "0f79791e-8135-442f-b890-0ae1b05786d6",
        "exehda-pub",
        pressao_reservatorio,
    )


def sensor_read():
    #    try:
    wdtimer.feed()
    sensor_read_simulated()
    global publication_payload
    global publication_topic
    gpio_port = 13
    temperature_sensor_pin = Pin(gpio_port)
    ds = ds18x20.DS18X20(onewire.OneWire(temperature_sensor_pin))
    temperature_sensor_list = ds.scan()
    ds.convert_temp()
    sensor_value_0 = ds.read_temp(temperature_sensor_list[0])
    sensor_value_1 = ds.read_temp(temperature_sensor_list[1])

    pub_sensor_value_0 = round(sensor_value_0, 2)
    pub_sensor_value_1 = round(sensor_value_1, 2)

    stack_pub(
        "publication",
        "12876483-61fe-4089-8d51-3059fd89631b",
        "exehda-pub",
        pub_sensor_value_0,
    )
    stack_pub(
        "publication",
        "d4a680e2-8918-40fc-820b-867ca99dae38",
        "exehda-pub",
        pub_sensor_value_1,
    )
    stack_pub("log", "", "exehda-teste", "DS3231: " + str(rtc_ds3231.get_time()))

    mqtt_publication()


#    except:
#        stack_pub("log", "exehda-pub", "Problems Reading Sensors - Publication Supressed")
#        mqtt_publication()

min00 = 0
min10 = 0
min20 = 0
min30 = 0
min40 = 0
min50 = 0


def scheduler(timer):
    minuto = time.localtime()[4]
    hora = time.localtime()[3]
    global min10
    global min20
    global min30
    global min40
    global min50
    global min00

    if (minuto == 10) & (min10 == 0):
        min10 = 1
        min00 = 0
        sensor_read()

    if (minuto == 20) & (min20 == 0):
        min20 = 1
        sensor_read()

    if (minuto == 30) & (min30 == 0):
        min30 = 1
        sensor_read()

    if (minuto == 40) & (min40 == 0):
        min40 = 1
        sensor_read()

    if (minuto == 50) & (min50 == 0):
        min50 = 1
        sensor_read()

    if (minuto == 00) & (min00 == 0):
        min00 = 1
        min10 = 0
        min20 = 0
        min30 = 0
        min40 = 0
        min50 = 0
        sensor_read()

    # Before restart save values in memory in files
    if (hora == 3) & (minuto == 5):
        time.sleep(60)
        # Topics:
        if len(publication_topic) > 0:
            file_sensor_topic = open("sensor_topic.txt", "w")
            while len(publication_topic) > 0:
                file_sensor_topic.write(str(publication_topic[0]))
                file_sensor_topic.write("\n")
                publication_topic.pop(0)
            file_sensor_topic.close()
        # Payloads:
        if len(publication_payload) > 0:
            file_sensor_payload = open("sensor_payload.txt", "w")
            while len(publication_payload) > 0:
                file_sensor_payload.write(str(publication_payload[0]))
                file_sensor_payload.write("\n")
                publication_payload.pop(0)
            file_sensor_payload.close()
        # Restart device
        machine.reset()


print("Timer started - 1.0 s")
tim0 = Timer(0)
tim0.init(period=1000, mode=Timer.PERIODIC, callback=scheduler)
