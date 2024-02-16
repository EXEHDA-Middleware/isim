### iSim Gateway

#### main.py 
* [Código do Gateway](https://github.com/exehdamiddleware/isim/blob/main/gateway/main.py) em uso na Abordagem iSim para coleta dos dados sensoriados nos reservatórios do SANEP

#### Informações Associadas ao Desenvolvimento do Código:

* https://docs.micropython.org/en/latest/library/os.html
* https://docs.micropython.org/en/latest/esp32/quickref.html
* [Manipulação de Arquivos em Python](https://www.guru99.com/python-file-readline.html)
* [Documentação Micropython sobre o Relógio da ESP32](https://docs.micropython.org/en/latest/library/machine.RTC.html#machine-rtc)
* [Como alimentar o kit de desenvolvimento com a ESP32](https://techexplorations.com/guides/esp32/begin/power/)
* Utilizando o Relógio DS3231:
  * [Exemplos de Códigos em Micropython](https://www.engineersgarage.com/micropython-esp8266-esp32-rtc-utc-local-time/)
  * [Pinagem](https://esp32io.com/tutorials/esp32-rtc)
* [Pinagem ESP 32 com 38 pinos](https://www.reddit.com/r/diyelectronics/comments/112dx6n/esp32_38_pin_pinout_cheat_sheet/?rdt=35959) - [Cópía local](https://github.com/exehdamiddleware/isim/blob/main/gateway/esp32-38-pin-pinout.png)

* Trabalhando com I2C:
  * https://electronics.stackexchange.com/questions/583433/is-it-possible-to-use-two-i2c-interfaces-with-the-esp32-using-micropython
  * [I2C em Micropython](https://docs.micropython.org/en/latest/library/machine.I2C.html)

* Sensor AHT25
  * Driver: https://github.com/etno712/aht/blob/main/README.md ([Outro exemplo com driver](https://forums.raspberrypi.com/viewtopic.php?t=343650))
  * [Datasheet do sensor AHT25](https://www.tinytronics.nl/en/sensors/air/humidity/asair-aht25-temperature-and-humidity-sensor-module-i2c) ([cópia local](https://github.com/exehdamiddleware/isim/blob/main/gateway/aht25-temperature-and-humidity-sensor.pdf))

* Sensor XDB305T
  * [Dados Fabricante](https://www.xdbsensor.com/xdb305t-industrial-pressure-transmitters-product/) - [Cópia Local](https://github.com/exehdamiddleware/isim/blob/main/gateway/XDB305T-G1-W5.pdf)
