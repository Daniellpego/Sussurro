<div align="center">

<img src="sussurro/assets/sussurro.png" alt="Sussurro icon" width="120">

# Sussurro

**Private, offline voice dictation for Windows.**<br>
Hold a hotkey, speak, release: the text appears in the app you are using.

[![CI](https://github.com/Daniellpego/Sussurro/actions/workflows/ci.yml/badge.svg)](https://github.com/Daniellpego/Sussurro/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Daniellpego/Sussurro?label=release)](https://github.com/Daniellpego/Sussurro/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/Daniellpego/Sussurro/total)](https://github.com/Daniellpego/Sussurro/releases)
[![MIT license](https://img.shields.io/github/license/Daniellpego/Sussurro)](LICENSE)

[Download](https://github.com/Daniellpego/Sussurro/releases/latest) ·
[Usage](#usage) ·
[Features](#features) ·
[Development](#development) ·
[Português](README.md)

<br>

<img src="docs/images/janela-principal.png" alt="Sussurro main window" width="340">
&nbsp;&nbsp;
<img src="docs/images/historico.png" alt="Transcription history" width="430">

</div>

> The interface and the voice commands are in Brazilian Portuguese. Whisper itself supports many languages: set `language` in `%APPDATA%\Sussurro\config.toml` to a code such as `en`, or to `auto`.

## Why Sussurro

- **Nothing leaves your computer.** Audio, transcripts and history stay local. There is no account, subscription or cloud transcription service.
- **Works in any app.** The text is pasted into the focused window, and your clipboard is restored afterwards.
- **Built for Brazilian Portuguese.** Spoken punctuation, a personal dictionary, and macros for spelled-out acronyms such as “esse tê efe” → STF and “ce pê éfe” → CPF.
- **Optional local AI rewriting.** Modes that clean up, formalize, summarize or translate the text run through Ollama, also on your machine.

## Sussurro compared with cloud dictation

| | Sussurro | Typical cloud dictation service |
|---|---|---|
| Where audio is processed | On your computer | On the provider's servers |
| Price | Free, MIT licensed | Usually a monthly subscription |
| Works offline after setup | Yes | No |
| AI rewriting | Local model through Ollama, optional | Provider's cloud model |
| Source code | Open | Closed |

## Install

Download an installer from the [latest release](https://github.com/Daniellpego/Sussurro/releases/latest):

| Installer | For |
|---|---|
| `SussurroSetup-CPU.exe` | Any computer, no graphics card needed |
| `SussurroSetup-CUDA.exe` | Computers with an NVIDIA GPU, for faster transcription |

On first run Sussurro downloads the transcription model and, if you want, installs Ollama and the rewriting model. After that everything works offline.

<details>
<summary><b>Verifying the installer and the SmartScreen warning</b></summary>

<br>

Each release includes `checksums-sha256.txt`. In PowerShell:

```powershell
Get-FileHash .\SussurroSetup-CPU.exe -Algorithm SHA256
```

Compare the result with the matching line in the checksums file.

The installers are not code-signed yet, so Windows may show “Windows protected your PC”. If the checksum matches, click **More info** and then **Run anyway**. The installers are built by the public [`release.yml`](.github/workflows/release.yml) workflow.

</details>

## Usage

1. Start Sussurro. It lives in the system tray.
2. Hold <kbd>Ctrl</kbd> + <kbd>Win</kbd> while you speak. A side mouse button can be used instead.
3. Release the keys. The text is transcribed and pasted at the cursor.

<p align="center">
  <img src="docs/images/hud-gravando.png" alt="Recording indicator" height="56">
  &nbsp;
  <img src="docs/images/hud-colado.png" alt="Text pasted" height="52">
</p>

Writing modes decide what happens to the text before it is pasted: Raw (verbatim), Clean, Email, Corporate email, Bullets, Prompt, Code, Translate (Portuguese → English), and templates for radiology reports (BI-RADS) and legal petitions. AI modes need Ollama. You can edit them and create your own.

## Features

- Local transcription with `faster-whisper` and Whisper `large-v3-turbo`.
- NVIDIA GPU with automatic fallback to CPU.
- Live preview in the indicator during longer recordings.
- Personal dictionary with suggested terms, and acronym macros (STF, STJ, OAB, CPF, CNPJ, RG).
- Searchable history of up to 500 transcriptions.
- Pasting that preserves the clipboard, including copied images and files.
- Start with Windows, light and dark themes, optional feedback sounds.

## Requirements

- Windows 10 build 19041 or later, or Windows 11.
- 8 GB of RAM for the CPU variant; 16 GB recommended for the AI modes.
- A built-in or USB microphone.
- A CUDA-compatible NVIDIA GPU, only for the CUDA variant.

## Development

Sussurro uses Python 3.11 or 3.12. In PowerShell:

```powershell
git clone https://github.com/Daniellpego/Sussurro.git
cd Sussurro
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt   # plus requirements-gpu.txt for NVIDIA
python -m sussurro
```

Before sending a change:

```powershell
ruff check sussurro scripts tests
python scripts/validate_all.py
pytest
```

The architecture is described in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and the helper scripts in [scripts/README.md](scripts/README.md) (both in Portuguese).

## Contributing

Bug reports, suggestions and pull requests are welcome, in English or Portuguese. Read [CONTRIBUTING.md](CONTRIBUTING.md) before you start, and report vulnerabilities privately as described in the [security policy](SECURITY.md).

## License

Released under the [MIT license](LICENSE). Licenses for the components bundled in the installers are listed in [docs/THIRD_PARTY_LICENSES.md](docs/THIRD_PARTY_LICENSES.md).
