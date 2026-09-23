# Sussurro

**English** · [Português](README.md)

Private, offline voice dictation for Windows. Hold a hotkey, speak, release, and the text is pasted into whatever app is in focus. Transcription runs on your machine with Whisper, and an optional local LLM through Ollama can clean up, formalize, summarize or translate what you said.

<p align="center">
  <img src="sussurro/assets/sussurro.png" alt="Sussurro icon" width="160">
</p>

<p align="center">
  <a href="https://github.com/Daniellpego/Sussurro/actions/workflows/ci.yml"><img src="https://github.com/Daniellpego/Sussurro/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/Daniellpego/Sussurro/releases/latest"><img src="https://img.shields.io/github/v/release/Daniellpego/Sussurro?label=release" alt="Latest release"></a>
  <a href="https://github.com/Daniellpego/Sussurro/releases"><img src="https://img.shields.io/github/downloads/Daniellpego/Sussurro/total" alt="Downloads"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Daniellpego/Sussurro" alt="MIT license"></a>
</p>

<!-- Demo: add a short GIF here (hold Ctrl+Win → speak → text appears), e.g. docs/demo.gif -->

## Why Sussurro

- **Nothing leaves your computer.** Audio, transcripts and history stay local. There is no account, subscription or cloud transcription service.
- **Works in any app.** The text is pasted into the focused window, and your clipboard is restored afterwards.
- **Fast on ordinary hardware.** It uses `faster-whisper` with the `large-v3-turbo` model on CPU or NVIDIA GPU, with automatic fallback to CPU. The model is warmed up before the hotkey is enabled, and partial text streams into the HUD during longer recordings.
- **Rewrites with a local LLM when you want it.** Clean, formal, summary and translation modes run through Ollama on `127.0.0.1`, and you can create your own modes with editable instructions.
- **Built for Brazilian Portuguese.** Spoken punctuation and paragraph commands, a personal dictionary, macros, and formatting for CPF, CNPJ and Brazilian court case numbers.

## Sussurro compared with cloud dictation

| | Sussurro | Typical cloud dictation service |
|---|---|---|
| Where audio is processed | On your computer | On the provider's servers |
| Price | Free, MIT licensed | Usually a monthly subscription |
| Works offline after setup | Yes | No |
| AI rewriting | Local model through Ollama, optional | Provider's cloud model |
| Custom rewrite modes | Yes, editable prompts | Varies |
| Source code | Open | Closed |

## Install

Download an installer from the [latest release](https://github.com/Daniellpego/Sussurro/releases/latest):

- `SussurroSetup-CPU.exe` runs without a dedicated GPU.
- `SussurroSetup-CUDA.exe` uses a compatible NVIDIA GPU to speed up transcription.

Each release includes `checksums-sha256.txt`. To verify an installer in PowerShell:

```powershell
Get-FileHash .\SussurroSetup-CPU.exe -Algorithm SHA256
```

Compare the result with the matching line in the checksums file for the same release.

### Windows SmartScreen warning

The installers are not code-signed yet, so Windows may show "Windows protected your PC" the first time you run one. Verify the SHA-256 checksum as described above and, if it matches, click **More info** and then **Run anyway**. The source code and the build pipeline that produces the installers are in this repository, in [`.github/workflows/release.yml`](.github/workflows/release.yml).

## Usage

1. Start Sussurro.
2. Hold `Ctrl+Win` while you speak. A side mouse button can be used instead.
3. Release the keys. The text is transcribed and pasted into the active window.

The system tray menu lets you switch the writing mode, open the history, pause capture and open the settings. Sussurro can also pick the mode automatically based on the app in focus.

## Language

The interface and the spoken commands are in Brazilian Portuguese, and the default transcription language is `pt`. Whisper itself supports many languages: set `language` in `%APPDATA%\Sussurro\config.toml` to another code such as `en`, or to `auto` for automatic detection. Help translating the interface and adding voice commands for other languages is welcome.

## Features

- Local transcription with `faster-whisper` and Whisper `large-v3-turbo`.
- CPU or NVIDIA GPU execution with automatic fallback to CPU.
- Spoken punctuation and paragraph commands in Portuguese.
- Personal dictionary, macros, and CPF, CNPJ and case number formatting.
- Local rewrite modes through Ollama, including clean text, formal, summary and translation.
- Custom modes with editable instructions.
- Automatic mode selection based on the focused app (optional).
- Searchable local history, capped at 500 entries.
- Global hotkey and side mouse button support.
- Paste into the active window with clipboard restoration.
- Per-step latency metrics written locally to `latency.jsonl`.

## Requirements

- Windows 10 build 19041 or later, or Windows 11.
- 8 GB of RAM for the CPU variant. 16 GB is recommended for larger models and Ollama.
- A built-in or USB microphone.
- A CUDA-compatible NVIDIA GPU, only for the CUDA variant.

Models are downloaded on first use, so an internet connection is needed during initial setup. After that, transcription and local rewriting work without sending dictated content to any server.

## Development

Sussurro uses Python 3.11 or 3.12 (the NumPy 1.x release its audio dependencies use has no Python 3.13 packages). In Windows PowerShell:

```powershell
git clone https://github.com/Daniellpego/Sussurro.git
cd Sussurro
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m sussurro
```

To also install the NVIDIA dependencies:

```powershell
pip install -r requirements-gpu.txt
```

Before sending a change:

```powershell
ruff check sussurro scripts tests
python scripts/validate_all.py
pytest
```

To measure transcription latency on your hardware with a WAV recording:

```powershell
python scripts/benchmark_latency.py sample.wav --device cpu
```

## Architecture

The app separates audio capture, transcription, post-processing, local LLM rewriting, storage and UI. The flow and each module's responsibilities are described in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (in Portuguese).

## Contributing

Bug reports and pull requests are welcome, in English or Portuguese. Read [CONTRIBUTING.md](CONTRIBUTING.md) before you start. Report vulnerabilities privately as described in the [security policy](SECURITY.md).

## License

Sussurro is released under the [MIT license](LICENSE). Licenses for the dependencies bundled in the installers are listed in [docs/THIRD_PARTY_LICENSES.md](docs/THIRD_PARTY_LICENSES.md).
