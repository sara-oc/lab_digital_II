from machine import Pin, PWM, I2C
from time import sleep_ms, ticks_ms, ticks_diff
import time
import dht
import math
import network
import urequests
import ujson
import utelegram
import _thread

from mpu6050 import MPU6050

# ==================================================
# WIFI
# ==================================================

red = "WIFI-ITM"
password = ""

wifi = network.WLAN(network.STA_IF)

# Reinicio del WiFi
wifi.active(False)
time.sleep(1)

wifi.active(True)
time.sleep(1)

# Conectar
wifi.connect(red, password)

while not wifi.isconnected():
    print("Conectando...")
    time.sleep(1)

print("CONECTADO")
print(wifi.ifconfig())


# ==================================================
# CONFIGURACION
# ==================================================


SERVER_IP = "172.16.225.45"

API_KEY = "nevera123"

POST_URL = "http://172.16.225.45:5000/datos"
GET_URL = "http://172.16.225.45:5000/config"

# ==================================================
# PINES
# ==================================================

PIN_DHT = 4
PIN_TOUCH = 13
PIN_HALL = 27
PIN_SERVO = 18
PIN_BUZZER = 23
PIN_PELTIER = 25

PIN_SDA = 21
PIN_SCL = 22


# ==================================================
# VARIABLES
# ==================================================

setpoint = 18.0

TEMP_MIN = 15.0
TEMP_MAX = 20.0

temperatura = 0
humedad = 0

estado_puerta = "ABIERTA"
puerta_cerrada = False
estado_bloqueo = "DESBLOQUEADA"
seguro_bloqueado = False

alerta = "NINGUNA"
alarma_puerta = False
alarma_movimiento = False

inclinacion = 0
movimiento_brusco = False
estado_movimiento = "ESTABLE"

tiempo_puerta_abierta = None


ultimo_touch = 0





# DHT22

sensor_dht = dht.DHT22(Pin(PIN_DHT))


# TOUCH

touch = Pin(PIN_TOUCH, Pin.IN)


# HALL

hall = Pin(PIN_HALL, Pin.IN)

# BUZZER

buzzer = PWM(Pin(PIN_BUZZER))
buzzer.duty(0)

# SERVO

servo = PWM(Pin(PIN_SERVO), freq=50)

ANG_BLOQUEADO = 70
ANG_DESBLOQUEADO = 150


def mover_servo(angulo):

    duty = int(25 + (angulo / 180) * 100)

    servo.duty(duty)


mover_servo(ANG_DESBLOQUEADO)


# PELTIER PWM

peltier = PWM(Pin(PIN_PELTIER))
peltier.freq(10)

salida_pid = 0


# MPU6050

i2c = I2C(
    0,
    scl=Pin(PIN_SCL),
    sda=Pin(PIN_SDA)
)

mpu = MPU6050(i2c)


# PID




error_anterior = 0
integral = 0

def activar_buzzer():

    for _ in range(2):
        buzzer.freq(1000)
        buzzer.duty(512)

        time.sleep(0.2)

        buzzer.duty(0)

        time.sleep(0.2)
        

#Telegram
        
ultimo_mensaje = ""

def handle_message(update):

    global ultimo_mensaje

    try:

        ultimo_mensaje = update["message"]["text"]

    except:

        pass



    


def controlar_temperatura(temp):
    
    kp = 180
    ki = 6
    kd = 10

    global integral
    global error_anterior

    error =  temp - setpoint
    
    if abs(error) < 4: # Empieza a acumular con fuerza cuando esté cerca
        integral += error
    else:
        integral = 0

    # 2. Límite de integral más alto (Anti-windup)
    # Dejamos que la integral pueda aportar hasta la mitad de la potencia total
    integral = max(-500, min(500, integral))
    
    derivada = error - error_anterior
    
    salida = (kp * error) + (ki * integral) + (kd * derivada)
    
    # 4. EL TRUCO DEL "PISO": Si todavía no llegamos, que no baje de 650 PWM
    if error > 0.2 and salida < 650:
        salida = 650 # Asegura al menos un 65% de potencia constante
    
    error_anterior = error
    
    if salida > 1023: salida = 1023
    if salida < 0: salida = 0

    pwm = int(salida)

    peltier.duty(pwm)

    porcentaje = pwm * 100 / 1023

    print("-----------------------")
    print("TEMP ACTUAL:", round(temp,2), "°C")
    print("SETPOINT:", setpoint, "°C")
    print("ERROR:", round(error,2))
    print("INTEGRAL:", round(integral,2))
    print("DERIVADA:", round(derivada,2))
    print("PWM:", pwm)
    print("POTENCIA:", round(porcentaje,1), "%")
    print("-----------------------")

# ENVIO FLASK


def enviar_datos():

    datos = {
        "alerta": alerta,
        "temperatura": round(temperatura,1),
        "humedad": round(humedad,1),
        "movimiento": estado_movimiento,
        "estado_puerta": estado_puerta,
        "estado_bloqueo": estado_bloqueo
    }

    try:

        r = urequests.post(
            POST_URL,
            json=datos,
            headers={
                "X-API-Key": API_KEY
            }
        )

        r.close()

    except Exception as e:

        print("ERROR WEB:", e)


# RECIBIR setpoint

def actualizar_setpoint():

    global setpoint

    try:

        r = urequests.get(GET_URL)

        datos = r.json()

        r.close()

        nuevo = float(
            datos["setpoint"]
        )

        if nuevo < TEMP_MIN:
            nuevo = TEMP_MIN

        if nuevo > TEMP_MAX:
            nuevo = TEMP_MAX

        setpoint = nuevo

    except:
        pass


# TEMPORIZADORES

t_dht = ticks_ms()
t_web = ticks_ms()
t_pid = ticks_ms()



# --------- LOOP PRINCIPAL---------------


while True:

    # TOUCH

    if touch.value():

        if ticks_diff(
            ticks_ms(),
            ultimo_touch
        ) > 500:

            ultimo_touch = ticks_ms()


            if seguro_bloqueado:

                mover_servo(
                    ANG_DESBLOQUEADO
                )

                seguro_bloqueado = False

                estado_bloqueo = "DESBLOQUEADA"

                enviar_datos()
                
        time.sleep(1)
        
    

    # =====================================
    # HALL
    # =====================================

    puerta_cerrada = hall.value()

    if puerta_cerrada:
        
        estado_puerta = "CERRADA"

        tiempo_puerta_abierta = None

        alarma_puerta = False
        
        alerta_puerta_enviada = False

        if not seguro_bloqueado:
            
            time.sleep(0.5)

            mover_servo(
                ANG_BLOQUEADO
            )

            seguro_bloqueado = True
            
            estado_bloqueo = "BLOQUEADA"

    else:
        
        estado_puerta = "ABIERTA"

        if tiempo_puerta_abierta is None:

            tiempo_puerta_abierta = ticks_ms()

        elif ticks_diff(
            ticks_ms(),
            tiempo_puerta_abierta
        ) > 30000:

            alarma_puerta = True
            alerta= "Puerta abierta"
            activar_buzzer()
            
        


    # DHT22


    if ticks_diff(
        ticks_ms(),
        t_dht
    ) > 1000:

        try:

            sensor_dht.measure()

            temperatura = (
                sensor_dht.temperature()
            )

            humedad = (
                sensor_dht.humidity()
            )

        except:
            pass

        t_dht = ticks_ms()



    # PID

    if ticks_diff(
        ticks_ms(),
        t_pid
    ) > 5000:

        controlar_temperatura(
            temperatura
        )

        t_pid = ticks_ms()



    # MPU6050


    ax, ay, az = mpu.get_accel()

    pitch = math.degrees(math.atan2(ax,math.sqrt(ay**2 + az**2)))

    roll = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))
    
    inclinacion = max(abs(pitch),abs(roll))

    aceleracion_total = math.sqrt(
        ax**2 + ay**2 + az**2)

    movimiento_brusco = (abs(aceleracion_total - 1) > 1)
       

    if movimiento_brusco:
        alerta = "Movimiento Brusco"
        enviar_datos()
        activar_buzzer()
    
    elif inclinacion > 30:
        alerta= "Cuidado, sistema inclinado"
        enviar_datos()
        activar_buzzer()
       
        
        
        
    if not alarma_puerta and inclinacion <= 30 and not movimiento_brusco:

        alerta = "NINGUNA"
        

    if movimiento_brusco or inclinacion >30:

        estado_movimiento = "MOVIMIENTO BRUSCO"

    else:

        estado_movimiento = "ESTABLE"


    # BUZZER



    # =====================================
    # WEB
    # =====================================

    if ticks_diff(
        ticks_ms(),
        t_web
    ) > 3000:

        enviar_datos()

        actualizar_setpoint()

        t_web = ticks_ms()
        
    
    sleep_ms(50)