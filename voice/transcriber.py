"""
Transcribes audio recordings in the recordings directory.
Uses MLX Whisper for transcription.
"""

import glob
import os
import time
from multiprocessing import Process, Queue
import mlx_whisper
from dotenv import load_dotenv
from utils import setup_process_logging, Config
from agent.voice_processor import process_transcriptions

load_dotenv()


def run_transcriber(logger, window_queue):
    """
    Transcribes audio recordings and sends them to LLM processor via queue.
    """
    setup_process_logging()

    transcription_queue = Queue(maxsize=Config.max_queue_size())
    processor = Process(
        target=process_transcriptions, args=(transcription_queue, window_queue, logger)
    )
    processor.start()

    logger.info("Starting transcriber")
    recordings_dir = os.path.join(Config.recordings_dir(), "*")
    transcribed = set()

    try:
        while True:
            files = sorted(
                glob.iglob(recordings_dir), key=os.path.getctime, reverse=True
            )
            if len(files) < 1:
                time.sleep(0.1)
                continue

            latest_recording = files[0]
            if os.path.exists(latest_recording) and latest_recording not in transcribed:
                logger.info(f"Transcribing {latest_recording}")
                try:
                    result = mlx_whisper.transcribe(
                        latest_recording,
                        path_or_hf_repo="mlx-community/whisper-small.en-mlx",
                    )
                    text = result["text"]
                    logger.info(f"Transcribed text: {text}")

                    transcription_queue.put(text)

                    os.remove(latest_recording)
                    transcribed.add(latest_recording)
                # pylint: disable=broad-exception-caught
                except Exception as e:
                    logger.error(
                        f"Error transcribing {latest_recording}: {str(e)}",
                        exc_info=True,
                    )

            time.sleep(0.1)
    # pylint: disable=broad-exception-caught
    except Exception as e:
        logger.error(f"Transcriber error: {str(e)}", exc_info=True)
    finally:
        processor.terminate()
        processor.join()


if __name__ == "__main__":
    from logging import getLogger

    logger_ = getLogger(__name__)
    run_transcriber(logger_, None)
