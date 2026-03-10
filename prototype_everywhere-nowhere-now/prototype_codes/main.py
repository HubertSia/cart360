from machine import Pin, I2C
from time import sleep, ticks_ms
import random

# Sound sensor on GP0
sound_sensor = Pin(0, Pin.IN, Pin.PULL_UP)

# 3 LEDs - representing emotional states
green = Pin(16, Pin.OUT)   # Calm / Peaceful
yellow = Pin(17, Pin.OUT)  # Agitated / Concerned  
red = Pin(18, Pin.OUT)     # Intense / Release

# LCD Setup
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)
devices = i2c.scan()
lcd_exists = False

if devices:
    lcd_address = devices[0]
    try:
        from pico_i2c_lcd import I2cLcd
        lcd = I2cLcd(i2c, lcd_address, 2, 16)
        lcd_exists = True
        print("LCD initialized")
    except:
        print("LCD library error")
else:
    print("No LCD detected")

# ICONS (using ASCII characters)
ICON_HEART = "\x7F"  # Using special character for heart (if supported)
ICON_WAVE = "~"
ICON_STAR = "*"
ICON_ARROW = ">"
ICON_CIRCLE = "o"
ICON_DOT = "."

# Welcome messages
welcome_messages = [
    "Your feelings",
    "are valid",
    "Release safely",
    "No judgment",
    "You are heard"
]

# Emotional messages by level
emotional_messages = {
    "CALM": [
        "~ peaceful ~",
        "* centered *",
        "~ calm seas ~",
        "* at ease *",
        "~ gentle wave ~"
    ],
    "AGITATED": [
        "> something up <",
        "~ rising tide ~",
        "* notice this *",
        "~ building wave ~",
        "> let it out <"
    ],
    "RELEASE": [
        "> release now <",
        "~ let go ~",
        "* you're safe *",
        "~ feel it ~",
        "> express <"
    ],
    "SILENT": [
        "* silence *",
        "~ breathe ~",
        "* rest here *",
        "~ be still ~",
        "* peaceful *"
    ]
}

# Post-messages after reading (shown for 3 seconds)
post_messages = {
    "CALM": [
        "You are centered",
        "Peace within you",
        "Calm and present",
        "Balanced energy",
        "Quiet strength"
    ],
    "AGITATED": [
        "It's okay to feel",
        "This too shall pass",
        "You're still safe",
        "Notice and release",
        "Valid feelings"
    ],
    "RELEASE": [
        "Well done",
        "Release complete",
        "You let it out",
        "Feel the freedom",
        "Expressed fully"
    ],
    "SILENT": [
        "Rest is good",
        "Silence heals",
        "Quiet moments",
        "Just breathe",
        "Stillness counts"
    ]
}

def reset_all_leds():
    """Explicitly turn off all LEDs"""
    green.off()
    yellow.off()
    red.off()
    print("LEDs reset - ready for next reading")

def show_startup():
    if not lcd_exists:
        return
    
    lcd.clear()
    for msg in welcome_messages:
        lcd.putstr(msg)
        sleep(1.2)
        lcd.clear()
    
    # Test LEDs at startup
    print("Testing LEDs...")
    green.on()
    sleep(0.5)
    green.off()
    yellow.on()
    sleep(0.5)
    yellow.off()
    red.on()
    sleep(0.5)
    red.off()
    print("LEDs ready")
    
    # Ready message
    lcd.putstr("Release your")
    lcd.move_to(0, 1)
    lcd.putstr("emotions here")
    sleep(2)
    lcd.clear()
    
    # Ready animation
    for i in range(3):
        lcd.putstr("Ready " + ICON_WAVE * i)
        sleep(0.3)
        lcd.clear()
        sleep(0.2)

def show_reading(level, count):
    """Show the live reading"""
    if not lcd_exists:
        return
    
    # First line - show intensity with icons
    lcd.move_to(0, 0)
    
    if level == "RELEASE":
        bars = ICON_HEART * min(8, int(count/10))
        lcd.putstr("Rls:{:3d} {}".format(count, bars))
    elif level == "AGITATED":
        waves = ICON_WAVE * min(8, int(count/8))
        lcd.putstr("Agt:{:3d} {}".format(count, waves))
    elif level == "CALM":
        dots = ICON_DOT * min(8, int(count/6))
        lcd.putstr("Calm:{:2d} {}".format(count, dots))
    else:
        lcd.putstr("....{:3d}....".format(count))
    
    # Second line - random emotional message
    lcd.move_to(0, 1)
    msg = random.choice(emotional_messages[level])
    lcd.putstr(msg + " " * (16 - len(msg)))

def show_post_message(level):
    """Show a post-reading message for 3 seconds"""
    if not lcd_exists:
        return
    
    lcd.clear()
    
    # Choose random post message
    msg = random.choice(post_messages[level])
    
    # Display with some formatting
    words = msg.split()
    if len(words) <= 2:
        # Short message - center it
        lcd.move_to((16 - len(msg)) // 2, 0)
        lcd.putstr(msg)
    else:
        # Longer message - split across two lines
        half = len(words) // 2
        line1 = " ".join(words[:half])
        line2 = " ".join(words[half:])
        lcd.move_to((16 - len(line1)) // 2, 0)
        lcd.putstr(line1)
        lcd.move_to((16 - len(line2)) // 2, 1)
        lcd.putstr(line2)
    
    # Add icon decoration
    if level == "RELEASE":
        lcd.move_to(0, 0)
        lcd.putstr(ICON_HEART)
        lcd.move_to(15, 1)
        lcd.putstr(ICON_HEART)
    elif level == "AGITATED":
        lcd.move_to(0, 0)
        lcd.putstr(ICON_WAVE)
        lcd.move_to(15, 1)
        lcd.putstr(ICON_WAVE)
    elif level == "CALM":
        lcd.move_to(0, 0)
        lcd.putstr(ICON_DOT)
        lcd.move_to(15, 1)
        lcd.putstr(ICON_DOT)
    
    sleep(3)
    lcd.clear()

# Run startup
if lcd_exists:
    show_startup()

print("Emotional Release Sound Meter Ready")
print("Green = Calm | Yellow = Agitated | Red = Release")
print("All feelings are welcome here")

# Variables
detection_count = 0
last_second = ticks_ms()
current_level = "SILENT"
session_count = 0
reading_phase = True  # True = showing reading, False = showing post-message
post_message_start = 0
cycle_count = 0

while True:
    current_time = ticks_ms()
    
    # Count every emotional expression (sound)
    if sound_sensor.value() == 0:
        detection_count += 1
    
    # Update every second (reading phase)
    if reading_phase and (current_time - last_second > 1000):
        cycle_count += 1
        print(f"\n--- CYCLE {cycle_count} STARTING ---")
        
        # STEP 1: RESET ALL LEDS (explicitly turn them off)
        reset_all_leds()
        
        # STEP 2: Determine emotional intensity level
        if detection_count > 10:
            # Light the RED LED only
            red.on()
            current_level = "RELEASE"
            print("RELEASE! (intensity: {})".format(detection_count))
        elif detection_count > 5:
            # Light the YELLOW LED only  
            yellow.on()
            current_level = "AGITATED"
            print("AGITATED (intensity: {})".format(detection_count))
        elif detection_count > 1:
            # Light the GREEN LED only
            green.on()
            current_level = "CALM"
            print("CALM (intensity: {})".format(detection_count))
        else:
            # All LEDs remain OFF
            current_level = "SILENT"
            print("SILENT (intensity: {})".format(detection_count))
        
        # Show which LED is active
        if current_level == "RELEASE":
            print("   → RED LED on")
        elif current_level == "AGITATED":
            print("   → YELLOW LED on")
        elif current_level == "CALM":
            print("   → GREEN LED on")
        else:
            print("   → No LEDs on (silent)")
        
        # Show reading on LCD
        if lcd_exists:
            show_reading(current_level, detection_count)
        
        # Prepare to show post-message
        reading_phase = False
        post_message_start = current_time
        
        # Increment session count for non-silent readings
        if current_level != "SILENT":
            session_count += 1
        
        # Reset counter for next reading
        detection_count = 0
        last_second = current_time
    
    # Post-message phase (show for 3 seconds)
    if not reading_phase and (current_time - post_message_start > 3000):
        print("--- POST-MESSAGE PHASE ---")
        
        # STEP 3: Turn off LEDs during post-message
        reset_all_leds()
        print("   → LEDs off for post-message")
        
        # Show post-message
        if lcd_exists and current_level != "SILENT":
            show_post_message(current_level)
        elif lcd_exists:
            # For silent, just show a quick message
            lcd.clear()
            lcd.putstr("Silence is")
            lcd.move_to(0, 1)
            lcd.putstr("okay too")
            sleep(2)
            lcd.clear()
        
        print(f"--- CYCLE {cycle_count} COMPLETE, READY FOR NEXT ---")
        print("Waiting for your next expression...\n")
        
        # STEP 4: Go back to reading phase (LEDs will be reset again at next cycle)
        reading_phase = True
    
    # Every 5 readings, show an encouraging summary
    if session_count > 0 and session_count % 5 == 0 and reading_phase and lcd_exists:
        # Quick flash of encouragement
        lcd.clear()
        lcd.putstr("You've expressed")
        lcd.move_to(0, 1)
        lcd.putstr("{} times ".format(session_count) + ICON_HEART)
        sleep(2)
        lcd.clear()
        session_count += 1  # Prevent repeating
    
    sleep(0.01)