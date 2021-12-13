from gpiozero import LED, PWMLED
from time import sleep 
from adafruit_bme280 import basic as adafruit_bme280
import busio
import board
import thingspeak


#connection to thingspeak
channel_id = XXX
write_key = 'XXX'
channel = thingspeak.Channel(id=channel_id, api_key=write_key)


def lpf(Ts, u_k1, V_k0):
    Tf = 5*Ts
    a = Ts/(Ts + Tf)
    V_k1 = (1 - a)*V_k0 + a*u_k1
    return V_k1

class bme280sensor:
    
    alarm = False
    
    def __init__(self):
        self.i2c = board.I2C()
        self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(self.i2c)
    
    def set_alarm(self, alarmlimit):
        self.alarm_lim = alarmlimit
        bme280sensor.alarm = True
    
    def get_temp(self, led):
        self.temp = self.bme280.temperature
        
        if bme280sensor.alarm == True:
            
            if(self.temp >= self.alarm_lim):
                led.value = 1
            else:
                led.value=0
            
            return self.temp
        else:
            led.value=0
            return self.temp
        
        
    
    def get_humidity(self):
        self.hum = self.bme280.humidity
        return self.hum
    
    def get_pressure(self):
        self.pres = self.bme280.pressure
        return self.pres
     

    

sensor = bme280sensor()
sensor.set_alarm(28)

led = PWMLED(16)
temp0 = 22.0
temp1 = 0.0
time_step = 15

while True:
    temp = sensor.get_temp(led)
    temp1 = lpf(time_step, temp, temp0)
    
    temp1 = round(temp1,2)
    
    response = channel.update({'field1': temp1})
    
    print(temp1)
    temp0 = temp1
    sleep(time_step)


    
        
