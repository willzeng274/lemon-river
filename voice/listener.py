"""
Stream audio from the microphone and save it to a WAV file.
"""

import datetime
import os
import sys
from collections import deque

import sounddevice as sd
import numpy as np
import wavio as wv
from utils import setup_process_logging, Config

# imported from .env
SAMPLE_RATE = Config.audio_recording_sample_rate()
CHUNK_DURATION = Config.audio_chunk_duration()
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
SILENCE_THRESHOLD = Config.audio_silence_threshold()
SILENCE_DURATION = Config.audio_silence_duration()
RECORDINGS_DIR = Config.recordings_dir()

os.makedirs(RECORDINGS_DIR, exist_ok=True)


def rms(data):
    """Calculate Root Mean Square (RMS) of audio data."""
    return np.sqrt(np.mean(np.square(data)))


def stream_record(logger):
    """Stream audio from the microphone and save it to a WAV file."""
    setup_process_logging()

    buffer = deque(maxlen=int(SILENCE_DURATION / CHUNK_DURATION))
    full_buffer = []
    is_recording = False
    speech_start_index = 0

    logger.info("Recording... Speak into the microphone.")
    logger.info(f"Using sample rate: {SAMPLE_RATE}, chunk size: {CHUNK_SIZE}")
    logger.info(
        f"Silence threshold: {SILENCE_THRESHOLD}, silence duration: {SILENCE_DURATION}s"
    )

    def callback(indata, _frames, _time, status):
        nonlocal is_recording, speech_start_index, full_buffer

        if status:
            logger.error("Error: %s", status)

        mono_data = indata.flatten()
        full_buffer.append(mono_data)
        buffer.append(mono_data)

        loudness = rms(mono_data)
        # logger.debug("Loudness: %f", loudness)
        has_speech = loudness > SILENCE_THRESHOLD

        if has_speech:
            if not is_recording:
                logger.info("Speech detected. Starting recording...")
                is_recording = True
                speech_start_index = len(full_buffer) - len(buffer)
        else:
            if (
                is_recording
                and len(buffer) == buffer.maxlen
                and all(rms(chunk) <= SILENCE_THRESHOLD for chunk in buffer)
            ):
                logger.info("Silence detected. Stopping recording.")
                save_recording(full_buffer[speech_start_index:], logger)
                buffer.clear()
                is_recording = False

    with sd.InputStream(
        callback=callback,
        channels=1,
        samplerate=SAMPLE_RATE,
        blocksize=CHUNK_SIZE,
        device=Config.microphone_index(),
    ):
        try:
            sd.sleep(sys.maxsize)
        except KeyboardInterrupt:
            logger.info("Recording interrupted by user.")
        finally:
            if is_recording:
                logger.info("Finalizing recording...")
                save_recording(full_buffer[speech_start_index:], logger)
            logger.info("Recording stopped.")


def save_recording(audio_data, logger):
    """Save the buffered audio to a WAV file."""
    if not audio_data:
        return
    audio_data = np.concatenate(audio_data)
    ts = datetime.datetime.now()
    filename = ts.strftime("%Y-%m-%d %H-%M-%S") + ".wav"
    file_path = os.path.join(RECORDINGS_DIR, filename)
    wv.write(file_path, audio_data, SAMPLE_RATE, sampwidth=2)
    logger.info("Saved recording to %s", file_path)


if __name__ == "__main__":
    from logging import getLogger

    logger_ = getLogger(__name__)
    stream_record(logger_)
