from gpiozero import LED, PWMLED, Button
from time import sleep 
from adafruit_bme280 import basic as adafruit_bme280
import busio
import board
import pymongo
from datetime import datetime
import paho.mqtt.client as mqtt

#Publish to MQTT

def get_password():
    with open('password.txt', 'r') as myfile:
        password=myfile.readlines()
    return password[0]


brokerAddress = "3e80ffc098e74e0ab89c32aec312f5ca.s2.eu.hivemq.cloud"
username = "actazeur"
password = get_password()
port = 8883

topic = "Sensor/Test1/Temp1"

def on_connect(client_mqtt, userdata, flags, rc):
    if rc == 0:
        print('connection successfull')
    else:
        print('connection unsuccessfull: ' + str(rc))

def on_message(client_mqtt, userdata, msg):
    print(f'Recieved message: {msg.topic} -> {msg.payload.decode("utf-8")}')
    

client_mqtt = mqtt.Client()
client_mqtt.on_connect = on_connect
client_mqtt.on_message = on_message

client_mqtt.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
client_mqtt.username_pw_set(username, password)
client_mqtt.connect(brokerAddress, port)

#connection to pymongo
client = pymongo.MongoClient("mongodb+srv://actazeur:oleerbest@cluster0.6rtgv.mongodb.net/raspdaq?retryWrites=true&w=majority")
mydb = client.raspdaq
mycol = mydb['temp']



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
    
    def get_temp(self, led, alarmstat, button):
        self.temp = self.bme280.temperature
        
        if bme280sensor.alarm == True:
            
            if(self.temp >= self.alarm_lim and alarmstat=='false'):
                led.value = 1
                alarmstat = 'active'
            elif(alarmstat == 'active' and button.is_pressed):
                alarmstat = 'aknowledged'
                led.value = 0.5
            elif(alarmstat == 'aknowledged' and self.temp < self.alarm_lim):
                alarmstat = 'false'
                led.value = 0

            
            return self.temp, alarmstat
        else:
            led.value=0
            return self.temp
        
        
    
    def get_humidity(self):
        self.hum = self.bme280.humidity
        return self.hum
    
    def get_pressure(self):
        self.pres = self.bme280.pressure
        return self.pres
     

def write_to_db(temperature, mycol, alarm):
    timestamp = datetime.now()
    mydict = {'temperature': temperature, 'time': timestamp, 'alarm_status': alarm}
    x = mycol.insert_one(mydict)

    

sensor = bme280sensor()
sensor.set_alarm(28)

alarm = 'false'
button = Button(23)

led = PWMLED(16)
temp0 = 22.0
temp1 = 0.0
time_step = 1

while True:
    temp, alarm = sensor.get_temp(led, alarm, button)
    temp1 = lpf(time_step, temp, temp0)
    
    temp1 = round(temp1,2)
    
    #write_to_db(temp1, mycol, alarm)
    
    print(temp1, alarm)
    client_mqtt.publish(topic, temp1)
    temp0 = temp1
    sleep(time_step)


    
        
