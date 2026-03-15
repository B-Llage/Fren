from __future__ import annotations

import io
import logging
import wave

import pygame

from .config import AUDIO_BUFFER_SIZE, AUDIO_SAMPLE_RATE, AUDIO_SILENCE_LEVEL, DEFAULT_SOUND_VOLUME, SOUND_EFFECT_SPECS

logger = logging.getLogger("virtual_pet")


def pre_init_audio() -> None:
    pygame.mixer.pre_init(AUDIO_SAMPLE_RATE, size=8, channels=1, buffer=AUDIO_BUFFER_SIZE)


def generate_square_wave_samples(
    frequency: int,
    duration_ms: int,
    amplitude: float,
    duty_cycle: float = 0.5,
    sample_rate: int = AUDIO_SAMPLE_RATE,
) -> bytes:
    sample_count = max(1, int((duration_ms / 1000.0) * sample_rate))
    if frequency <= 0 or amplitude <= 0:
        return bytes([AUDIO_SILENCE_LEVEL]) * sample_count

    cycle_length = max(1, int(round(sample_rate / frequency)))
    high_length = max(1, int(round(cycle_length * duty_cycle)))
    high_value = min(255, AUDIO_SILENCE_LEVEL + int(round(127 * amplitude)))
    low_value = max(0, AUDIO_SILENCE_LEVEL - int(round(127 * amplitude)))
    samples = bytearray(sample_count)

    for sample_index in range(sample_count):
        cycle_index = sample_index % cycle_length
        samples[sample_index] = high_value if cycle_index < high_length else low_value

    return bytes(samples)


def build_sound_effect(
    notes: list[tuple[int, int, float]],
    duty_cycle: float = 0.5,
    gap_ms: int = 0,
) -> pygame.mixer.Sound | None:
    if pygame.mixer.get_init() is None:
        return None

    pcm_frames = bytearray()
    for frequency, duration_ms, amplitude in notes:
        pcm_frames.extend(generate_square_wave_samples(frequency, duration_ms, amplitude, duty_cycle=duty_cycle))
        if gap_ms > 0:
            pcm_frames.extend(generate_square_wave_samples(0, gap_ms, 0.0))

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(1)
        wav_file.setframerate(AUDIO_SAMPLE_RATE)
        wav_file.writeframes(pcm_frames)

    wav_buffer.seek(0)
    try:
        return pygame.mixer.Sound(file=wav_buffer)
    except pygame.error:
        logger.exception("Failed to build sound effect.")
        return None


def load_sound_effects() -> dict[str, pygame.mixer.Sound]:
    if pygame.mixer.get_init() is None:
        logger.warning("Audio mixer is unavailable; sound effects are disabled.")
        return {}

    sound_effects: dict[str, pygame.mixer.Sound] = {}
    for sound_name, spec in SOUND_EFFECT_SPECS.items():
        sound = build_sound_effect(
            spec["notes"],
            duty_cycle=spec.get("duty_cycle", 0.5),
            gap_ms=spec.get("gap_ms", 0),
        )
        if sound is None:
            continue

        sound.set_volume(spec.get("volume", 0.4))
        sound_effects[sound_name] = sound

    return sound_effects


class AudioManager:
    def __init__(self) -> None:
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init(AUDIO_SAMPLE_RATE, size=8, channels=1, buffer=AUDIO_BUFFER_SIZE)
            except pygame.error:
                logger.warning("Unable to initialize audio mixer; continuing without sound.", exc_info=True)

        self.base_volumes = {sound_name: spec.get("volume", 0.4) for sound_name, spec in SOUND_EFFECT_SPECS.items()}
        self.sound_effects = load_sound_effects()
        self.master_volume = DEFAULT_SOUND_VOLUME
        self.set_master_volume(self.master_volume)

    def set_master_volume(self, master_volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, float(master_volume)))
        for sound_name, sound in self.sound_effects.items():
            try:
                sound.set_volume(self.base_volumes.get(sound_name, 0.4) * self.master_volume)
            except pygame.error:
                logger.warning("Failed to set volume for sound effect '%s'.", sound_name, exc_info=True)

    def play(self, sound_name: str) -> None:
        sound = self.sound_effects.get(sound_name)
        if sound is None:
            return

        try:
            sound.play()
        except pygame.error:
            logger.warning("Failed to play sound effect '%s'.", sound_name, exc_info=True)
