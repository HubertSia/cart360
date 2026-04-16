from machine import Pin, I2C, ADC
from time import sleep, ticks_ms
import random
import math  

# === SOUND SENSOR ===
# Initialize the sound sensor on the Pico’s analog input GP26 (ADC0)
sound_sensor = ADC(26)

# === LED SETUP ===
# Assign each LED (green, yellow, red) to specific GPIO pins for visual sound-level feedback
green = Pin(16, Pin.OUT)
yellow = Pin(17, Pin.OUT)
red = Pin(18, Pin.OUT)

# === LCD SETUP ===
# Use hardware I2C on port 0, with SCL on GP9 and SDA on GP8
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)

# Scan I2C bus for devices — identifies if an LCD is connected
devices = i2c.scan()
lcd_exists = False

# If an I2C LCD is found, try to initialize it
if devices:
    lcd_address = devices[0]
    try:
        from pico_i2c_lcd import I2cLcd  # import LCD helper class

        lcd = I2cLcd(i2c, lcd_address, 2, 16)  # create 2x16 LCD object
        lcd_exists = True
        print("LCD initialized at", hex(lcd_address))
    except Exception as e:
        print("LCD library error:", e)
else:
    print("No LCD detected")

# === ICON DEFINITIONS ===
# These are small display symbols used to decorate messages
ICON_WHEEL = "@"
ICON_SLICE = "-"
ICON_DRIP = "~"
ICON_HEART = "\x7F"

# === STARTUP / WELCOME MESSAGES ===
welcome_messages = [
    "Sweet dreams",
    "are made of cheese",
    "Who am I to",
    "diss a brie?",
]

# === MESSAGE POOLS FOR EACH SOUND STATE ===
# Funny cheese-themed phrases corresponding to sound “mood”
cheese_messages = {
    "CALM": [
        "~ brie‑zy day ~",
        "* mellow cheddar *",
        "~ easy slice ~",
        "* stay grate‑ful *",
        "~ calm curd ~",
    ],
    "AGITATED": [
        "> getting melty <",
        "~ turning fondue ~",
        "* stir it up *",
        "~ cheesy tension ~",
        "> bubble & release <",
    ],
    "RELEASE": [
        "> full fondue! <",
        "~ let the brie flow ~",
        "* gooey relief *",
        "~ you’re goud‑a ~",
        "> release the rind <",
    ],
    "SILENT": [
        "* rest in rind *",
        "~ breathe n’ brie ~",
        "* hush the churn *",
        "~ quiet cheddar ~",
        "* be still curd *",
    ],
}

# Post message pool — shown after each reading
post_messages = {
    "CALM": [
        "Soft & centered",
        "Peace‑feta within",
        "Cheddar calm",
        "Creamy balance",
        "Goud‑a vibes",
    ],
    "AGITATED": [
        "It’s okay to melt",
        "Fondue & release",
        "Still grate‑ful",
        "Smooth again soon",
        "Cheese the moment",
    ],
    "RELEASE": [
        "That was legen‑dairy",
        "Melt complete",
        "Let it brie",
        "You are un‑brie‑lievable",
        "Full release",
    ],
    "SILENT": [
        "Quiet rind time",
        "Silence is goud‑a",
        "Rest that curd",
        "Just breathe",
        "Still cheese inside",
    ],
}

# === HELPER FUNCTIONS ===

# Turn off all LEDs
def reset_all_leds():
    green.off()
    yellow.off()
    red.off()

# LCD startup animation + initialization sequence
def show_startup():
    if not lcd_exists:
        return
    lcd.clear()
    for msg in welcome_messages:
        lcd.putstr(msg)
        sleep(1.2)
        lcd.clear()
    lcd.putstr("Stay grate‑ful")
    lcd.move_to(0, 1)
    lcd.putstr("Take it cheesy :)")
    sleep(2)
    lcd.clear()

    # Flash LEDs one by one
    for led in [green, yellow, red]:
        led.on()
        sleep(0.4)
        led.off()

    # Display ready message
    lcd.putstr("PSRC v1.5")
    lcd.move_to(0, 1)
    lcd.putstr("Ready to melt")
    sleep(2)
    lcd.clear()

# Display live sound readings on LCD in pseudo‑dB with icons
def show_reading(level, avg_value):
    if not lcd_exists:
        return
    lcd.clear()
    lcd.move_to(0, 0)

    # Approximate decibel conversion and scaling
    ref_level = 15000
    ratio = avg_value / ref_level if ref_level > 0 else 1
    if ratio <= 0:
        db_value = 0
    else:
        raw_db = 20 * math.log10(ratio)
        db_value = raw_db * 1.6 + 20  # scaling to fit display range
    db_value = int(max(0, min(db_value, 99)))  # clamp to 0–99 dB

    # Build simple “bar graph” for visual feedback
    bar_units = min(int(avg_value / 8000), 8)

    # Choose display label & symbol depending on level
    if level == "RELEASE":
        label = "Fondue"
        bar = ICON_DRIP * bar_units
    elif level == "AGITATED":
        label = "Melty"
        bar = ICON_SLICE * bar_units
    elif level == "CALM":
        label = "Briezy"
        bar = ICON_WHEEL * bar_units
    else:
        label = "Silent"
        bar = ""

    # Show the line and a random message underneath
    if level != "SILENT":
        lcd.putstr(f"{label}:{db_value:2d}dB {bar}"[:16])
    else:
        lcd.putstr("Silent curd")

    lcd.move_to(0, 1)
    msg = random.choice(cheese_messages[level])
    lcd.putstr(msg[:16])

# Show secondary message after reading phase
def show_post_message(level):
    if not lcd_exists:
        return
    lcd.clear()
    msg = random.choice(post_messages[level])

    # Split message across one or two lines depending on length
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
    lcd.move_to(0, 0)
    lcd.putstr(ICON_WHEEL)
    sleep(3)
    lcd.clear()

# === STARTUP SEQUENCE ===
if lcd_exists:
    show_startup()

print("PSRC ready for use!.")
print("Green = Calm Brie | Yellow = Melty | Red = Full Fondue")
print("Stay grate‑ful.")

# === RUNTIME VARIABLES ===
sound_total = 0           # total of sound readings collected
samples = 0               # number of readings per interval
last_second = ticks_ms()  # used to time intervals
current_level = "SILENT"
session_count = 0
reading_phase = True
post_message_start = 0
cycle_count = 0

# === MAIN LOOP ===
# Continuously reads sound, computes average once per second, and reacts.
while True:
    current_time = ticks_ms()
    sound_total += sound_sensor.read_u16()  # add new reading (0–65535)
    samples += 1

    # Every 1 second: evaluate average sound to categorize level
    if reading_phase and (current_time - last_second > 1000):
        cycle_count += 1
        reset_all_leds()
        avg_sound = sound_total // samples
        sound_total = 0
        samples = 0

        print(f"\n--- SLICE {cycle_count} ---")
        print("Average sound:", avg_sound)

        # Determine which LED / “cheese mood” to show
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

        print("Cheese level:", current_level)

        if lcd_exists:
            show_reading(current_level, avg_sound)

        reading_phase = False  # move to post-message phase
        post_message_start = current_time
        if current_level != "SILENT":
            session_count += 1
        last_second = current_time

    # === POST-MESSAGE PHASE ===
    # After a few seconds, display closing / positive messages
    if not reading_phase and (current_time - post_message_start > 3000):
        reset_all_leds()
        if lcd_exists and current_level != "SILENT":
            show_post_message(current_level)
        elif lcd_exists:
            lcd.clear()
            lcd.putstr("Quiet curd stills")
            lcd.move_to(0, 1)
            lcd.putstr("Let it brie")
            sleep(2)
            lcd.clear()

        # Occasionally display an affirmation
        if lcd_exists and random.random() < 0.20:
            lcd.clear()
            lcd.putstr("Stay grate‑ful!")
            lcd.move_to(0, 1)
            lcd.putstr("You are brie‑lliant")
            sleep(3)
            lcd.clear()

        print(f"--- Slice {cycle_count} complete ---")
        reading_phase = True  # prepare for next reading cycle

    # Every 5 sound sessions, display a summary message
    if (
        session_count > 0
        and session_count % 5 == 0
        and reading_phase
        and lcd_exists
    ):
        lcd.clear()
        lcd.putstr("You’ve melted")
        lcd.move_to(0, 1)
        lcd.putstr(f"{session_count} times")
        sleep(2)
        lcd.clear()
        session_count += 1  # increment to avoid repeating same message

    sleep(0.01)  # small delay to reduce CPU load