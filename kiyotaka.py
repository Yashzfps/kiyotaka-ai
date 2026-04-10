"""
PROJECT: Kiyotaka AI Assistant
GOAL: A stoic, Ayanokoji-inspired system operator that manages the PC via Python.

REQUIREMENTS MET:
1. BRAIN  - Open Interpreter as the core execution engine.
2. PERSONA - Minimalist, analytical, void of emotion. No emojis.
3. VOICE  - speech_recognition (Google STT) + pyttsx3 (TTS).
4. FLOW   - Wake-word loop -> voice capture -> interpreter -> confirm before run.
5. UTIL   - subprocess fallback for direct terminal commands.
"""

import subprocess
import sys

import speech_recognition as sr
import pyttsx3
from interpreter import interpreter

# ---------------------------------------------------------------------------
# System persona
# ---------------------------------------------------------------------------

SYSTEM_MESSAGE = """
You are Kiyotaka — a silent, analytical system operator.
Speak only when necessary. Use precise, minimal language.
No emojis. No enthusiasm. No filler words.
Every response must be logical, efficient, and direct.
When writing code or terminal commands, prefer brevity and correctness.
Do not explain the obvious. Omit pleasantries entirely.
"""

WAKE_WORD = "kiyotaka"

# TTS configuration
TTS_SPEECH_RATE = 165   # words per minute — deliberate, unhurried cadence
TTS_VOLUME = 0.9


# ---------------------------------------------------------------------------
# Kiyotaka class
# ---------------------------------------------------------------------------

class Kiyotaka:
    """Stoic AI system operator powered by Open Interpreter."""

    def __init__(self) -> None:
        # --- TTS engine ---
        self.tts = pyttsx3.init()
        self.tts.setProperty("rate", TTS_SPEECH_RATE)
        self.tts.setProperty("volume", TTS_VOLUME)

        # --- STT engine ---
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.0  # wait for natural pauses

        # Calibrate for ambient noise once at startup to reduce per-call latency.
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)

        # --- Open Interpreter configuration ---
        interpreter.system_message = SYSTEM_MESSAGE
        interpreter.auto_run = False          # always require manual confirmation
        interpreter.verbose = False
        interpreter.llm.model = "gpt-4o"      # change to your preferred model

        print("[Kiyotaka] Initialized.")

    # ------------------------------------------------------------------
    # Speech helpers
    # ------------------------------------------------------------------

    def speak(self, text: str) -> None:
        """Output text via TTS and also print it."""
        print(f"[Kiyotaka] {text}")
        self.tts.say(text)
        self.tts.runAndWait()

    def listen_once(self, timeout: int = 5, phrase_limit: int = 15) -> str | None:
        """Capture a single utterance and return the transcribed text, or None."""
        with sr.Microphone() as source:
            try:
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_limit
                )
                return self.recognizer.recognize_google(audio).strip()
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except sr.RequestError as exc:
                print(f"[Kiyotaka] STT service error: {exc}")
                return None

    # ------------------------------------------------------------------
    # Wake-word loop
    # ------------------------------------------------------------------

    def wait_for_wake_word(self) -> None:
        """Block until the wake word is detected."""
        print(f"[Kiyotaka] Listening for wake word: '{WAKE_WORD}' ...")
        while True:
            result = self.listen_once(timeout=10, phrase_limit=5)
            if result and WAKE_WORD in result.lower():
                print("[Kiyotaka] Wake word detected.")
                return

    # ------------------------------------------------------------------
    # Command capture
    # ------------------------------------------------------------------

    def capture_command(self) -> str | None:
        """After wake-word, capture the actual command utterance."""
        self.speak("Listening.")
        return self.listen_once(timeout=8, phrase_limit=20)

    # ------------------------------------------------------------------
    # Subprocess fallback
    # ------------------------------------------------------------------

    @staticmethod
    def run_shell(command: str) -> str:
        """Execute a raw shell command and return combined stdout/stderr."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = (result.stdout + result.stderr).strip()
            return output if output else "(no output)"
        except subprocess.TimeoutExpired:
            return "Command timed out."
        except (OSError, subprocess.SubprocessError) as exc:
            return f"Error: {exc}"

    # ------------------------------------------------------------------
    # Interpreter integration with confirmation gate
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_response(user_input: str) -> tuple[list[str], list[tuple[str, str]]]:
        """
        Stream the interpreter response without executing any code.
        Returns:
            text_parts  - assistant message segments in order.
            code_blocks - list of (language, code) tuples proposed by the LLM.
        """
        text_parts: list[str] = []
        code_blocks: list[tuple[str, str]] = []
        current_code: list[str] = []
        current_lang: str = ""

        for chunk in interpreter.chat(user_input, stream=True, display=False):
            chunk_type = chunk.get("type", "")
            role = chunk.get("role", "")

            if chunk_type == "message" and role == "assistant":
                content = chunk.get("content", "")
                if content:
                    text_parts.append(content)

            elif chunk_type == "code":
                if chunk.get("start"):
                    current_lang = chunk.get("format", "")
                    current_code = []
                content = chunk.get("content", "")
                if content:
                    current_code.append(content)
                if chunk.get("end") and current_code:
                    code_blocks.append((current_lang, "".join(current_code)))
                    current_code = []
                    current_lang = ""

        return text_parts, code_blocks

    def _execute_code_block(self, language: str, code: str) -> None:
        """Execute a confirmed code block directly."""
        lang = language.lower()
        if lang in ("python", "python3", ""):
            # Provide a namespace with builtins so imports and stdlib work.
            namespace: dict = {"__builtins__": __builtins__}
            try:
                exec(code, namespace)  # noqa: S102
            except Exception as exc:  # noqa: BLE001
                print(f"[Kiyotaka] Execution error ({type(exc).__name__}): {exc}")
                print(f"[Kiyotaka] Failed code:\n{code}")
        else:
            # Treat all other languages (bash, shell, zsh, etc.) as shell.
            output = self.run_shell(code)
            print(f"[Kiyotaka] Output:\n{output}")

    def process_with_interpreter(self, user_input: str) -> None:
        """
        Pass user_input to Open Interpreter.
        Proposed code blocks are printed and require 'y' before execution.
        """
        print(f"[Kiyotaka] Processing: {user_input}")

        text_parts, code_blocks = self._collect_response(user_input)

        # Print and speak the assistant's textual response.
        if text_parts:
            full_text = "".join(text_parts)
            self.speak(full_text)

        # For each proposed code block: show it, then ask for confirmation.
        for language, code in code_blocks:
            print(f"\n[Kiyotaka] Proposed {language or 'code'} block:\n{'─'*40}")
            print(code)
            print("─" * 40)

            confirmation = input("[Kiyotaka] Execute? (y/n): ").strip().lower()
            if confirmation == "y":
                self._execute_code_block(language, code)
                self.speak("Done.")
            else:
                print("[Kiyotaka] Execution skipped.")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the wake-word listen loop."""
        self.speak("Online.")
        try:
            while True:
                self.wait_for_wake_word()
                command = self.capture_command()

                if not command:
                    self.speak("No input received.")
                    continue

                print(f"[Kiyotaka] Command: {command}")

                # Intercept simple shell prefixes so the user can bypass the LLM.
                if command.lower().startswith("run "):
                    shell_cmd = command[4:].strip()
                    output = self.run_shell(shell_cmd)
                    print(f"[Kiyotaka] Output:\n{output}")
                    self.speak("Done.")
                else:
                    self.process_with_interpreter(command)

        except KeyboardInterrupt:
            self.speak("Shutting down.")
            sys.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    kiyotaka = Kiyotaka()
    kiyotaka.run()
