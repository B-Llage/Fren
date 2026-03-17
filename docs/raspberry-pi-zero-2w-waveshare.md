## Raspberry Pi Zero 2 W + Waveshare 1.3inch LCD HAT

The game now supports two runtime modes from the same entry point:

- Desktop: normal `pygame` window with keyboard input.
- Waveshare HAT: direct ST7789 SPI output plus GPIO button input.

### Runtime behavior

- Windows and other non-Pi systems default to the desktop profile.
- Raspberry Pi systems auto-detect into the `waveshare-hat` profile with direct SPI output enabled.
- You can override either mode:

```bash
python3 virtual_pet_template.py --platform desktop
python3 virtual_pet_template.py --platform waveshare-hat
python3 virtual_pet_template.py --platform waveshare-hat --display-rotation 180
python3 virtual_pet_template.py --platform waveshare-hat --windowed --no-direct-output
```

### Controls

- Desktop next: `Q`, `Down`, `Right`, `Tab`
- Desktop previous: `A`, `Up`, `Left`
- Desktop confirm: `W`, `Enter`, `Space`
- Desktop back: `E`, `Escape`, `Backspace`

- HAT previous: joystick `Up` or `Left`
- HAT next: joystick `Down` or `Right`, `KEY1`
- HAT confirm: joystick press, `KEY2`
- HAT back: `KEY3`

If you use `--display-rotation`, the joystick directions are remapped to follow the rotated screen.

In 2x2 grid menus such as `Feed`, directional inputs now move by row and column instead of cycling linearly.

### HAT-only display setting

When the direct Waveshare output backend is active, the in-game `Option` menu includes:

- `Auto Upd`: enables a startup `git pull` check on Raspberry Pi clones of this repo
- `Color`: cycles panel saturation between `Normal`, `Rich`, `Vivid`, and `Boost`
- `Contrast`: cycles panel contrast between `Normal`, `Rich`, `Punchy`, and `Arcade`

`Auto Upd` is off by default. When you turn it on, the launcher checks GitHub on startup, fast-forwards the local checkout if a new commit exists, and then restarts into the updated code.

### Pi setup

1. Follow the official Waveshare HAT setup first:
   - Enable SPI in `sudo raspi-config`.
   - Add `gpio=6,19,5,26,13,21,20,16=pu` to your boot config so the HAT inputs have pull-ups.
2. Install the Python dependencies for the direct SPI display path:

```bash
sudo apt update
sudo apt install -y git python3-pygame python3-gpiozero python3-lgpio python3-numpy python3-spidev
```

3. Copy this repo to the Pi.
4. Start the game from the repo root:

```bash
python3 virtual_pet_template.py --platform waveshare-hat
```

If Raspberry Pi auto-detection is working, `python3 virtual_pet_template.py` is also enough.

If the screen is upside down or rotated, retry with:

```bash
python3 virtual_pet_template.py --platform waveshare-hat --display-rotation 180
```

If you prefer to keep using Waveshare's framebuffer/X11 display setup instead of direct SPI output:

```bash
python3 virtual_pet_template.py --platform waveshare-hat --no-direct-output
```

### Auto update behavior

The built-in updater is intentionally conservative:

- It only runs on a detected Raspberry Pi.
- It only runs if `Option -> Auto Upd` is set to `On`.
- It only runs from a real git clone with an upstream branch configured.
- It skips the update if the repo has local code changes. The save file is preserved across the update.

If you want startup updates under `systemd`, keep the service pointing at `virtual_pet_template.py`; the launcher handles the update check before the game starts.

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
