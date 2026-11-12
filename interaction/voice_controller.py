"""Offline, asynchronous Vosk recognition. No audio is sent to a server."""

import json
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Event, Thread


SPELLS = {
    "lumos": "activate",
    "invisibility": "activate",
    "nox": "deactivate",
    "reveal": "reveal",
}


def parse_spell(text):
    # Require an exact command, avoiding substring activations in conversation.
    return SPELLS.get(text.strip().lower())


class VoiceController:
    def __init__(self, model_path=None):
        self.model_path = model_path
        self.commands = Queue(maxsize=8)
        self.status = "Voice off"
        self._stop = Event()
        self._thread = None

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.running:
            return
        if not self.model_path or not Path(self.model_path).is_dir():
            raise ValueError("Select an unpacked offline Vosk model with --voice-model PATH")
        self._stop.clear()
        self.status = "Voice loading"
        self._thread = Thread(target=self._listen, daemon=True, name="marauder-voice")
        self._thread.start()

    def _listen(self):
        try:
            import sounddevice as sd
            from vosk import KaldiRecognizer, Model

            model = Model(self.model_path)
            recognizer = KaldiRecognizer(model, 16000, json.dumps([*SPELLS, "[unk]"]))
            audio = Queue(maxsize=12)

            def callback(data, frames, time, status):
                if status:
                    self.status = f"Voice audio: {status}"
                try:
                    audio.put_nowait(bytes(data))
                except Full:
                    pass  # Drop stale input instead of growing memory.

            with sd.RawInputStream(
                samplerate=16000, blocksize=4000, dtype="int16", channels=1, callback=callback
            ):
                self.status = "Voice listening (offline)"
                while not self._stop.is_set():
                    try:
                        data = audio.get(timeout=0.2)
                    except Empty:
                        continue
                    if recognizer.AcceptWaveform(data):
                        command = parse_spell(json.loads(recognizer.Result()).get("text", ""))
                        if command:
                            try:
                                self.commands.put_nowait(command)
                            except Full:
                                pass
        except Exception as error:
            self.status = f"Voice unavailable: {error}"
        finally:
            if self._stop.is_set():
                self.status = "Voice off"

    def poll(self):
        result = []
        while True:
            try:
                result.append(self.commands.get_nowait())
            except Empty:
                return result

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        self.poll()
        if not self.running:
            self.status = "Voice off"
