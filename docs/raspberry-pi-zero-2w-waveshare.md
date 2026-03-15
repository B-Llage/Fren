## Raspberry Pi Zero 2 W + Waveshare 1.3inch LCD HAT

The game now supports two runtime modes from the same entry point:

- Desktop: normal `pygame` window with keyboard input.
- Waveshare HAT: fullscreen launch with optional GPIO button input.

### Runtime behavior

- Windows and other non-Pi systems default to the desktop profile.
- Raspberry Pi systems auto-detect into the `waveshare-hat` profile.
- You can override either mode:

```bash
python3 virtual_pet_template.py --platform desktop
python3 virtual_pet_template.py --platform waveshare-hat
python3 virtual_pet_template.py --platform waveshare-hat --windowed
```

### Controls

- Desktop next: `Q`, `Down`, `Right`, `Tab`
- Desktop previous: `A`, `Up`, `Left`
- Desktop confirm: `W`, `Enter`, `Space`
- Desktop back: `E`, `Escape`, `Backspace`

- HAT previous: joystick `Up` or `Left`, `KEY1`
- HAT next: joystick `Down` or `Right`
- HAT confirm: joystick press, `KEY2`
- HAT back: `KEY3`

### Pi setup

1. Follow the official Waveshare HAT setup first:
   - Enable SPI in `sudo raspi-config`.
   - Add `gpio=6,19,5,26,13,21,20,16=pu` to your boot config so the HAT inputs have pull-ups.
   - If you are using Waveshare's FBCP desktop mirroring path, their wiki says it is for 32-bit Raspberry Pi OS, not 64-bit.
2. If your display is already working, keep that setup and just install the Python dependencies for this game:

```bash
sudo apt update
sudo apt install -y python3-pygame python3-gpiozero python3-lgpio
```

3. Copy this repo to the Pi.
4. Start the game from the repo root:

```bash
python3 virtual_pet_template.py --platform waveshare-hat
```

If Raspberry Pi auto-detection is working, `python3 virtual_pet_template.py` is also enough.

### Optional autostart on the Pi desktop

Create `~/.config/autostart/fren.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Fren
Exec=/usr/bin/python3 /home/pi/Fren/virtual_pet_template.py --platform waveshare-hat
Path=/home/pi/Fren
Terminal=false
```

Adjust `/home/pi/Fren` if you cloned the repo elsewhere.
