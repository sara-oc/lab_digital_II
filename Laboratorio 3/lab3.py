from machine import ADC, Pin, Timer
import time

# HARDWARE
sensor = ADC(Pin(34))
sensor.atten(ADC.ATTN_11DB)
sensor.width(ADC.WIDTH_12BIT)

led = Pin(2, Pin.OUT)

# FILTROS
N = 5
buffer_prom = [0]*N
indice_prom = 0

def prom_movil(x):
    global indice_prom
    buffer_prom[indice_prom] = x
    indice_prom = (indice_prom + 1) % N
    return sum(buffer_prom)/N

buffer_mediana = [0]*5

def filtro_mediana(x):
    global buffer_mediana
    buffer_mediana = buffer_mediana[1:] + [x]
    temp = sorted(buffer_mediana)
    return temp[len(temp)//2]

alpha = 0.2
prev_exp = 0

def filtro_exp(x):
    global prev_exp
    y = alpha*x + (1-alpha)*prev_exp
    prev_exp = y
    return y

# CONFIGURACIÓN
def configurar():
    global frecuencia, Ts_ms, filtros_activos

    print("CONFIGURACION")

    frecuencia = float(input("Introduzca la frecuencia de muestreo (Hz): "))
    Ts_ms = int(1000 / frecuencia)

    print("\nFiltros disponibles:")
    print("1 -> Promedio movil")
    print("2 -> Mediana")
    print("3 -> Exponencial")

    filtros_activos = []
    
    while True:
        n = int(input("Cantidad de filtros a usar (1-3): "))

        if n == 3:
            filtros_activos = [1,2,3]
            break

        elif n == 1 or n == 2:
            for i in range(n):
                while True:
                    opcion = int(input(f"Seleccione el filtro #{i+1}: "))
                    if opcion in [1,2,3] and opcion not in filtros_activos:
                        filtros_activos.append(opcion)
                        break
                    else:
                        print("Opcion invalida o repetida")
            break
        else:
            print("Opcion invalida")

    print("Filtros seleccionados:", filtros_activos)
    print("Configuracion lista\n")

#  LM35 
def leer_lm35():
    adc = sensor.read()
    voltaje = adc * (3.3 / 4095)
    return voltaje * 100

# Variables del timer
ultima_muestra = 0
nueva_muestra = False

def muestrear(timer):
    global ultima_muestra, nueva_muestra
    ultima_muestra = leer_lm35()
    nueva_muestra = True

# MAIN
def main():
    global nueva_muestra

    configurar()

    print("Iniciando adquisicion...")
    print("cruda,filtrada")

    archivo = open("datos.txt", "w")
    archivo.write("cruda,filtrada\n")

    duracion = float(input("Duracion de la adquisicion (segundos): "))
    
    # Cuenta regresiva
    conteo = 5
    print("Duracion establecida:", duracion, "segundos")
    for i in range(5):
        print("Inicio en:", conteo)
        conteo -= 1
        time.sleep(1)

    
    timer = Timer(0)
    timer.init(period=Ts_ms, mode=Timer.PERIODIC, callback=muestrear)

    inicio = time.time()

    while time.time() - inicio < duracion:

        if nueva_muestra:
            nueva_muestra = False

            led.value(1)

            cruda = ultima_muestra
            valor = cruda

            # Filtros en cascada
            for filtro in filtros_activos:
                if filtro == 1:
                    valor = prom_movil(valor)
                elif filtro == 2:
                    valor = filtro_mediana(valor)
                elif filtro == 3:
                    valor = filtro_exp(valor)

            print("{:.2f},{:.2f}".format(cruda, valor))
            archivo.write("{:.2f},{:.2f}\n".format(cruda, valor))

            led.value(0)

    timer.deinit()

    archivo.close()
    print("Adquisicion finalizada")

# RUN
main()