# Mond AI

**The Silent Architect of Your OS**

Mond AI is a stoic system operator designed to eliminate friction between human thought and digital execution. Inspired by the clinical precision of Ayanokōji, this agent bypasses the flashy, talkative nature of modern LLMs in favor of raw analytical power.

---

## Features

| Capability | Detail |
|---|---|
| **Brain** | [Open Interpreter](https://github.com/OpenInterpreter/open-interpreter) — LLM-powered code generation and execution |
| **Voice input** | `speech_recognition` with Google STT |
| **Voice output** | `pyttsx3` offline TTS |
| **Wake word** | Say *"mond"* to activate |
| **Safety gate** | Proposed code is printed; you type `y` to execute or `n` to skip |
| **Shell fallback** | Prefix a command with `run ` to bypass the LLM and run it directly via `subprocess` |

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Yashzfps/kiyotaka-ai.git
cd kiyotaka-ai
```

### 2. Install system dependencies

**Ubuntu / Debian**

```bash
sudo apt install portaudio19-dev python3-pyaudio espeak
```

**macOS (Homebrew)**

```bash
brew install portaudio espeak
```

**Windows**

Install [PortAudio](http://www.portaudio.com/) and ensure a working microphone is available.

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your LLM API key

Open Interpreter uses your OpenAI key by default (model: `gpt-4o`). Export it before running:

```bash
export OPENAI_API_KEY="sk-..."
```

To use a different model, edit the `interpreter.llm.model` line in `kiyotaka.py`.

---

## Usage

```bash
python kiyotaka.py
```

1. Mond AI will say *"Online."* and start listening.
2. Say **"mond"** to trigger it.
3. Speak your command — e.g. *"list all running processes"*.
4. Any proposed code block is printed. Type **`y`** and press Enter to execute, or **`n`** to skip.
5. Press **Ctrl+C** to exit cleanly.

### Direct shell bypass

Prefix spoken commands with **"run"** to skip the LLM entirely:

> "mond" → "run ls -la"

---

## Project structure

```
kiyotaka-ai/
├── kiyotaka.py       # Main implementation
├── requirements.txt  # Python dependencies
└── README.md
```

---

## Persona

Mond AI communicates with minimal, analytical language. No emojis. No filler. Every word serves a purpose.
