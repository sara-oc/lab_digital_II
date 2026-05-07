from machine import Pin, I2C, PWM
import ssd1306
import time
import random

# ---------------- OLED ----------------
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# ---------------- BOTONES ----------------
btn_up = Pin(14, Pin.IN, Pin.PULL_UP)
btn_down = Pin(27, Pin.IN, Pin.PULL_UP)
btn_enter = Pin(26, Pin.IN, Pin.PULL_UP)

# ---------------- BUZZER ----------------
buzzer = PWM(Pin(25))
buzzer.duty(0)

# ---------------- ESTADOS ----------------
MENU = 0
PLAYING = 1
PAUSE = 2
GAME_OVER = 3

state = MENU

# ---------------- MODOS ----------------
MODES = ["CLASICO", "CONTRARELOJ", "HARDCORE"]
selected = 0
mode = 0

# ---------------- JUGADOR ----------------
player_x = 30
player_y = 32
float_offset = 0
float_dir = 1

# tamaño real del sprite
PLAYER_W = 10
PLAYER_H = 9

# ---------------- SPRITES ----------------
SPRITE = [
"0000011100",
"0000100010",
"0001000101",
"0001000101",
"0001000001",
"0010000001",
"1100000001",
"0100101010",
"0011010100",
]

bat_1 = [
"0101010",
"1011101",
"0001000",
]

bat_2 = [
"1101011",
"0011100",
"0001000",
]

grave_1 = [
"001100",
"010010",
"100001",
"100001",
"100001",
"100001",
]

grave_2 = [
"000111000",
"001000100",
"010010010",
"100111001",
"100010001",
"100010001",
"100000001",
"100000001",
"100000001",
]

grave_3 = [
"00011000",
"00011000",
"11111111",
"11111111",
"00011000",
"00011000",
"00011000",
"00011000",
"00011000",
"00011000",
"00011000",
]

# ---------------- JUEGO ----------------
obstacles = []
score = 0
start_time = 0
speed = 3
spawn_rate = 1200

# ---------------- PAUSA ----------------
pause_option = 0
PAUSE_OPTIONS = ["CONTINUAR", "SALIR"]

# ---------------- MUSICA ----------------
melody = [523, 659, 784, 659]
note_index = 0
NOTE_DURATION = 200  # ms
next_note_time = 0

def play_music():
    global note_index, next_note_time

    now = time.ticks_ms()

    if time.ticks_diff(now, next_note_time) >= 0:
        buzzer.freq(melody[note_index])
        buzzer.duty(120)

        note_index = (note_index + 1) % len(melody)
        next_note_time = time.ticks_add(now, NOTE_DURATION)

def stop_sound():
    buzzer.duty(0)

def collision_sound():
    for f in range(1500, 300, -200):
        buzzer.freq(f)
        buzzer.duty(300)
        time.sleep_ms(30)
    buzzer.duty(0)

# ---------------- INPUT ----------------
def pressed(btn):
    return btn.value() == 0

# ---------------- DIBUJO SPRITES ----------------
def draw_sprite(sprite, x, y):
    x = int(x)
    y = int(y)

    for r, row in enumerate(sprite):
        for c, px in enumerate(row):
            if px == '1':
                oled.pixel(x + c, y + r, 1)

# ---------------- MENU ----------------
def draw_menu():
    oled.fill(0)
    oled.text("BOO MODE!", 20, 0)

    for i, m in enumerate(MODES):
        y = 20 + i*12
        if i == selected:
            oled.text(">", 10, y)
        oled.text(m, 20, y)

    oled.show()

# ---------------- PAUSA ----------------
def draw_pause():
    oled.fill(0)
    oled.text("PAUSA", 40, 5)

    for i, opt in enumerate(PAUSE_OPTIONS):
        y = 25 + i*12
        if i == pause_option:
            oled.text(">", 10, y)
        oled.text(opt, 30, y)

    oled.show()

# ---------------- CUENTA ----------------
def countdown():
    for i in [3,2,1]:
        oled.fill(0)
        oled.text("START", 40, 20)
        oled.text(str(i), 60, 40)
        oled.show()
        time.sleep(1)


# ---------------- OBSTACULOS ----------------
GROUND_Y = 58
YELLOW_LIMIT = 15
GAME_TOP = 16
grave_1_h = len(grave_1)
grave_2_h = len(grave_2)
grave_3_h = len(grave_3)

def spawn_obstacle():
    tipo = random.choice(["bat","grave"])

    if tipo == "bat":
        y = random.randint(GAME_TOP,40)
        grave_type = None
    else:
        grave_type = random.choice([1,2,3])

        if grave_type == 1:
            y = GROUND_Y - len(grave_1)
        elif grave_type == 2:
            y = GROUND_Y - len(grave_2)
        else:
            y = GROUND_Y - len(grave_3)

    obstacles.append({
        "x":128,
        "y":y,
        "type":tipo,
        "grave_type":grave_type,
        "frame":0,
        "passed":False
        })


def update_obstacles():
    global obstacles, score

    for o in obstacles:
        o["x"] -= speed

        # animación murciélago
        if o["type"] == "bat":
            o["frame"] ^= 1

        # score
        if not o["passed"] and o["x"] < player_x:
            score += 1
            o["passed"] = True

    obstacles = [o for o in obstacles if o["x"] > -10]

# ---------------- COLISION ----------------
def check_collision():
    for o in obstacles:

        if o["type"] == "bat":
            w, h = 7, 3

        else:
            if o["grave_type"] == 1:
                w, h = 6, 6
            elif o["grave_type"] == 2:
                w, h = 9, 9
            else:
                w, h = 8, 11

        if (player_x < o["x"] + w and
            player_x + PLAYER_W > o["x"] and
            player_y < o["y"] + h and
            player_y + PLAYER_H > o["y"]):
            return True
    return False

# ---------------- DIBUJO ----------------


def draw_game():
    oled.fill(0)

    #suelo
    oled.hline(0,56, 128, 1)

    oled.hline(0, YELLOW_LIMIT, 128, 1)
    oled.hline(0, YELLOW_LIMIT-2, 128, 1)

    # tiempo
    elapsed = time.ticks_diff(time.ticks_ms(), start_time)//1000

    if mode == 1:
        t = max(0, 30 - elapsed)
    else:
        t = elapsed

    oled.text("Score:"+str(score), 0, 0)
    oled.text("Time:"+str(t), 70, 0)

    # jugador
    draw_sprite(SPRITE, player_x, int(player_y))

    # obstaculos
    for o in obstacles:
        if o["type"] == "bat":
            sprite = bat_1 if o["frame"] else bat_2
            draw_sprite(sprite, o["x"], o["y"])

        else:
            if o["grave_type"] == 1:
                draw_sprite(grave_1, o["x"], o["y"])
            elif o["grave_type"] == 2:
                draw_sprite(grave_2, o["x"], o["y"])
            else:
                draw_sprite(grave_3, o["x"], o["y"])

    oled.show()

# ---------------- LOOP ----------------
last_update = time.ticks_ms()
last_spawn = time.ticks_ms()
last_difficulty_update = time.ticks_ms()

while True:
    
    if state == MENU:
        draw_menu()

        if pressed(btn_up):
            selected = (selected-1)%3
            time.sleep_ms(200)

        if pressed(btn_down):
            selected = (selected+1)%3
            time.sleep_ms(200)

        if pressed(btn_enter):
            mode = selected
            obstacles = []
            score = 0
            player_y = 32

            # 👇 CONFIG POR MODO
            if mode == 0:  # CLASICO
                speed = 3
                spawn_rate = 1500

            elif mode == 1:  # CONTRARRELOJ
                speed = 3
                spawn_rate = 1200

            else:  # HARDCORE
                speed = 5
                spawn_rate = 900

            countdown()
            start_time = time.ticks_ms()
            state = PLAYING

            last_difficulty_update = time.ticks_ms()

    elif state == PLAYING:

        now = time.ticks_ms()
        play_music()

        elapsed = time.ticks_diff(now, start_time) // 1000

        # pausa
        if pressed(btn_enter):
            stop_sound() 
            state = PAUSE
            time.sleep_ms(300)

        # movimiento
        if pressed(btn_up):
            player_y -= 2
        if pressed(btn_down):
            player_y += 2

        # limites
        player_y = max(GAME_TOP, min(GROUND_Y - PLAYER_H, player_y))

        # flotación
        float_offset += float_dir * 0.5
        if abs(float_offset) > 3:
            float_dir *= -1
        player_y += float_dir * 0.3

        # spawn
        if time.ticks_diff(now, last_spawn) > spawn_rate:
            spawn_obstacle()
            last_spawn = now

        update_obstacles()

        if check_collision():
            stop_sound()
            collision_sound() 
            state = GAME_OVER

        if mode == 1 and (time.ticks_diff(now, start_time)//1000) >= 30:
            stop_sound()
            state = GAME_OVER

        if time.ticks_diff(now, last_difficulty_update) > 5000:
            speed = min(speed + 1, 50)
            spawn_rate = max(300, spawn_rate - 200)
            last_difficulty_update = now

        draw_game()

    elif state == PAUSE:
        draw_pause()

        if pressed(btn_up):
            pause_option = (pause_option-1)%3
            time.sleep_ms(200)

        if pressed(btn_down):
            pause_option = (pause_option+1)%3
            time.sleep_ms(200)

        if pressed(btn_enter):
            if pause_option == 0:  # continuar
                next_note_time = time.ticks_ms()
                state = PLAYING
            else:  # salir
                state = MENU

            time.sleep_ms(300)

    elif state == GAME_OVER:
        oled.fill(0)

        elapsed = time.ticks_diff(time.ticks_ms(), start_time)//1000
        t = max(0, 30-elapsed) if mode==1 else elapsed

        oled.text("GAME OVER", 22, 18)
        oled.text("Score:"+str(score), 30, 35)
        oled.text("Time:"+str(t), 30, 50)

        oled.show()
        time.sleep(3)
        state = MENU