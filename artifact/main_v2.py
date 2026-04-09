from machine import Pin, I2C, ADC
from time import sleep, ticks_ms
import random

# === SOUND SENSOR ===
# Use analog input (on GP26 / ADC0)
sound_sensor = ADC(26)

# === LED SETUP ===
green = Pin(16, Pin.OUT)   # Calm / Peaceful
yellow = Pin(17, Pin.OUT)  # Agitated / Concerned
red = Pin(18, Pin.OUT)     # Intense / Release

# === LCD SETUP ===
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)
devices = i2c.scan()
lcd_exists = False

if devices:
    lcd_address = devices[0]
    try:
        from pico_i2c_lcd import I2cLcd

        lcd = I2cLcd(i2c, lcd_address, 2, 16)
        lcd_exists = True
        print("LCD initialized at address", hex(lcd_address))
    except Exception as e:
        print("LCD library error:", e)
else:
    print("No LCD detected")


# === ICONS ===
ICON_HEART = "\x7F"  # special char for heart (if supported)
ICON_WAVE = "~"
ICON_DOT = "."
ICON_ARROW = ">"


# === WELCOME MESSAGES ===
welcome_messages = [
    "Your feelings",
    "are valid",
    "Release safely",
    "No judgment",
    "You are heard",
]

# === EMOTIONAL MESSAGES ===
emotional_messages = {
    "CALM": [
        "~ peaceful ~",
        "* centered *",
        "~ calm seas ~",
        "* at ease *",
        "~ gentle wave ~",
    ],
    "AGITATED": [
        "> something up <",
        "~ rising tide ~",
        "* notice this *",
        "~ building wave ~",
        "> let it out <",
    ],
    "RELEASE": [
        "> release now <",
        "~ let go ~",
        "* you're safe *",
        "~ feel it ~",
        "> express <",
    ],
    "SILENT": [
        "* silence *",
        "~ breathe ~",
        "* rest here *",
        "~ be still ~",
        "* peaceful *",
    ],
}

# === POST-READING MESSAGES ===
post_messages = {
    "CALM": [
        "You are centered",
        "Peace within you",
        "Calm and present",
        "Balanced energy",
        "Quiet strength",
    ],
    "AGITATED": [
        "It's okay to feel",
        "This too shall pass",
        "You're still safe",
        "Notice and release",
        "Valid feelings",
    ],
    "RELEASE": [
        "Well done",
        "Release complete",
        "You let it out",
        "Feel the freedom",
        "Expressed fully",
    ],
    "SILENT": [
        "Rest is good",
        "Silence heals",
        "Quiet moments",
        "Just breathe",
        "Stillness counts",
    ],
}


# === UTILITIES ===
def reset_all_leds():
    """Turn off all LEDs"""
    green.off()
    yellow.off()
    red.off()


def show_startup():
    if not lcd_exists:
        return

    lcd.clear()
    for msg in welcome_messages:
        lcd.putstr(msg)
        sleep(1.2)
        lcd.clear()

    # Test LEDs
    print("Testing LEDs...")
    for led in [green, yellow, red]:
        led.on()
        sleep(0.4)
        led.off()
    print("LEDs tested successfully")

    # Show ready message
    lcd.putstr("Release your")
    lcd.move_to(0, 1)
    lcd.putstr("emotions here")
    sleep(2)
    lcd.clear()

    for i in range(3):
        lcd.putstr("Ready " + ICON_WAVE * i)
        sleep(0.3)
        lcd.clear()
        sleep(0.2)


def show_reading(level, avg_value):
    """Show the current emotional intensity"""
    if not lcd_exists:
        return

    lcd.clear()
    lcd.move_to(0, 0)

    # Represent intensity visually
    bar_units = int(avg_value / 8000)
    bar_units = min(bar_units, 8)

    if level == "RELEASE":
        lcd.putstr("Rls:{} {}".format(avg_value // 1000, ICON_HEART * bar_units))
    elif level == "AGITATED":
        lcd.putstr("Agt:{} {}".format(avg_value // 1000, ICON_WAVE * bar_units))
    elif level == "CALM":
        lcd.putstr("Calm:{} {}".format(avg_value // 1000, ICON_DOT * bar_units))
    else:
        lcd.putstr("Silent")

    lcd.move_to(0, 1)
    msg = random.choice(emotional_messages[level])
    lcd.putstr(msg[:16])


def show_post_message(level):
    """Show a calming reflection for 3 seconds"""
    if not lcd_exists:
        return

    lcd.clear()
    msg = random.choice(post_messages[level])
    words = msg.split()

    if len(words) <= 2:
        lcd.move_to((16 - len(msg)) // 2, 0)
        lcd.putstr(msg)
    else:
        half = len(words) // 2
        line1 = " ".join(words[:half])
        line2 = " ".join(words[half:])
        lcd.move_to((16 - len(line1)) // 2, 0)
        lcd.putstr(line1)
        lcd.move_to((16 - len(line2)) // 2, 1)
        lcd.putstr(line2)

    # Icon decoration
    if level == "RELEASE":
        lcd.move_to(0, 0)
        lcd.putstr(ICON_HEART)
    elif level == "AGITATED":
        lcd.move_to(0, 0)
        lcd.putstr(ICON_WAVE)
    elif level == "CALM":
        lcd.move_to(0, 0)
        lcd.putstr(ICON_DOT)

    sleep(3)
    lcd.clear()


# === STARTUP ===
if lcd_exists:
    show_startup()

print("Analog Emotional Sound Meter ready.")
print("Green = Calm | Yellow = Agitated | Red = Release")
print("All feelings are welcome here.")

# === VARIABLES ===
sound_total = 0
samples = 0
last_second = ticks_ms()
current_level = "SILENT"
session_count = 0
reading_phase = True
post_message_start = 0
cycle_count = 0


# === MAIN LOOP ===
while True:
    current_time = ticks_ms()

    # Collect analog samples continuously
    sound_total += sound_sensor.read_u16()
    samples += 1

    # Update every second (reading phase)
    if reading_phase and (current_time - last_second > 1000):
        cycle_count += 1
        reset_all_leds()

        avg_sound = sound_total // samples
        sound_total = 0
        samples = 0

        print(f"\n--- CYCLE {cycle_count} ---")
        print("Average sound:", avg_sound)

        # Emotional thresholds (tune to your sensor sensitivity)
        if avg_sound > 55000:
            red.on()
            current_level = "RELEASE"
        elif avg_sound > 40000:
            yellow.on()
            current_level = "AGITATED"
        elif avg_sound > 25000:
            green.on()
            current_level = "CALM"
        else:
            current_level = "SILENT"

        print("Current level:", current_level)

        if lcd_exists:
            show_reading(current_level, avg_sound)

        reading_phase = False
        post_message_start = current_time

        if current_level != "SILENT":
            session_count += 1

        last_second = current_time

    # POST-MESSAGE PHASE
    if not reading_phase and (current_time - post_message_start > 3000):
        reset_all_leds()

        if lcd_exists and current_level != "SILENT":
            show_post_message(current_level)
        elif lcd_exists:
            lcd.clear()
            lcd.putstr("Silence is")
            lcd.move_to(0, 1)
            lcd.putstr("okay too")
            sleep(2)
            lcd.clear()

        print(f"--- Cycle {cycle_count} complete ---")
        reading_phase = True

    # Encouragement summary
    if (
        session_count > 0
        and session_count % 5 == 0
        and reading_phase
        and lcd_exists
    ):
        lcd.clear()
        lcd.putstr("You've expressed")
        lcd.move_to(0, 1)
        lcd.putstr(f"{session_count} times {ICON_HEART}")
        sleep(2)
        lcd.clear()
        session_count += 1  # prevent repeating

    sleep(0.01)