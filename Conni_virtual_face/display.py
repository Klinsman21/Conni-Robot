import os

# Caminhos
BRIGHTNESS_PATH = "/sys/class/backlight/10-0045/brightness"
MAX_BRIGHTNESS_PATH = "/sys/class/backlight/10-0045/max_brightness"

def get_max_brightness():
    with open(MAX_BRIGHTNESS_PATH, "r") as f:
        return int(f.read().strip())

def set_brightness(value):
    try:
        with open(BRIGHTNESS_PATH, "w") as f:
            f.write(str(value))
    except PermissionError:
        print("⚠️ Você precisa rodar o script como root (use sudo).")