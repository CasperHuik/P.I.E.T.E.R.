######################################################################
########################P.I.E.T.E.R.##################################
######################################################################
#In dit programma wordt de werking van PIETER geregeld
#Hierin worden de functies van het toevoegen van water, voeding, wegen en een fotomaken geregeld

#Schrijver: Casper Huikeshoven



#### Modules ##########################################################

import os 
import glob
import datetime
import RPi.GPIO as GPIO
import cv2
import pigpio
from time import sleep
from instabot import Bot
import sys
from hx711 import HX711

#### Variabelen ########################################################

imgNum = 3
cap = cv2.VideoCapture(0)

# GPIO pins waarop de componenten zijn aangesloten 
drukKnop = 22 #vlotterschakelaar
kraan1 = 17 #elektrische kraan
servo = 19 #mg995

#weegsensor variablen
EMULATE_HX711=False
referenceUnit = -2118
hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(referenceUnit)
gewicht = 0

# GPIO setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#GPIO pins setup voor elk component
GPIO.setup(servo,GPIO.OUT) #servo motor ingestelt op output
GPIO.setup(drukKnop,GPIO.IN, pull_up_down=GPIO.PUD_UP) #Vlotterschakelaar ingesteld op input met een pull up
GPIO.setup(kraan1,GPIO.OUT) #Elektrische kraan ingesteld op output

#servomotor van de plantenvoedingsspuit ingesteld op 50hz volgens de datasheet van de mg995
servo1 = pigpio.pi()
servo1.set_mode(servo, pigpio.OUTPUT)
servo1.set_PWM_frequency(servo, 50)

duty = 500 #start rotatie van servomotor


#### Bij opstarten ###############################################################

#kraan dicht
GPIO.output(kraan1,True) 

#instagrambot inloggen
cookie_del = glob.glob("config/*cookie.json")
os.remove(cookie_del[0])
bot = Bot() 
bot.login(username="pieterpws", password="Huts123!")

# Tijd gegeven en gezegd dat er begonnen is
t=datetime.datetime.now()
print(t.hour, t.minute, t.second)
print("proces beginnen")

# 
hx.reset()
hx.tare()


####  Voedings programma #########################################################

def voedingtoevoegen():
    global duty

    duty+=20
    servo1.set_servo_pulsewidth(servo, duty)
    sleep(1)

#### Foto programma ##############################################################

def fotoMakenEnVersturen():
    global imgNum
    global kraan1
    global gewicht

    GPIO.output(kraan1,True)   
    
    print("foto zal gemaakt worden binnerkort")

    while True:
        for ii in range(10):
            ret,img = cap.read()
        cv2.imwrite('/home/pi/images/'+str(imgNum)+'.jpg',img)
        break

    image = '/home/pi/images/'+str(imgNum)+'.jpg'
    imgcaption = "Dag: "+ str(imgNum) + " Gewicht: " + str(gewicht) + "gram"
    bot.upload_photo(image, caption=imgcaption) 
    imgNum = imgNum + 1
    
    sleep(60)

def wegen():
    val = hx.get_weight(5)
    hx.power_down()
    hx.power_up()
    sleep(0.1)
    return val
    
#### Loop ##################################################################

try: 
    while True:
        gewicht = round(wegen())
        t=datetime.datetime.now() #TIjd op elk moment
        if(GPIO.input(drukKnop) == False): 
            GPIO.output(kraan1,True) #kraan dicht
        else:
            GPIO.output(kraan1,False) #kraan open
            voedingtoevoegen() #voedingsspuit aan

        if(t.hour == 13 and t.minute == 00):
            fotoMakenEnVersturen() #foto maken en versturen elke dag om 13:00uur

#### stoppen #################################################################

except KeyboardInterrupt: #ctrl + c
    print('Gestopt')
    servo1.set_PWM_dutycycle(servo, 0)
    servo1.set_PWM_frequency(servo, 0)
    cv2.destroyAllWindows()
    GPIO.cleanup()
    sys.exit()