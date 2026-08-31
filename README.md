# Sussurro

Aplicativo desktop **local-first para Windows** que transforma voz em texto com push-to-talk. O Sussurro captura o microfone, transcreve localmente com `faster-whisper`, pode refinar o texto com um LLM local via Ollama e cola o resultado no aplicativo que estava em foco.

> A inferência é local. Internet pode ser necessária no primeiro uso para baixar os modelos.

## Funcionalidades

- Push-to-talk global por `Ctrl+Win` ou botão do mouse.
- Transcrição local com `faster-whisper`.
- Fallback automático de GPU para CPU quando CUDA não está disponível.
- Modos editáveis de escrita, incluindo modo Raw sem LLM.
- Integração opcional com Ollama e Qwen 2.5 para refinamento local.
- Pós-processamento determinístico e comandos de voz para quebras/pontuação.
- Colagem automática no app em foco com múltiplas estratégias de fallback.
- HUD flutuante sem roubar o foco da janela de destino.
- Histórico local de transcrições.
- Dicionário do usuário para termos, nomes e jargões.
- Tray icon, onboarding, ajustes, temas claro/escuro e autostart opcional.

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| UI | PySide6 / Qt |
| ASR | faster-whisper / CTranslate2 |
| Áudio | sounddevice, soundfile, NumPy |
| Hotkeys | pynput |
| Clipboard/entrada | pyperclip, keyboard, Win32 SendInput |
| LLM opcional | Ollama local via HTTPX |
| Modelos | Hugging Face Hub / Ollama |
| Build | PyInstaller |
| Instalador | Inno Setup 6 |

## Requisitos

- Windows 10 ou Windows 11.
- Python 3.11 recomendado para desenvolvimento.
- Microfone reconhecido pelo Windows.
- GPU NVIDIA é opcional, mas recomendada para menor latência.
- Ollama é opcional. Sem ele, o modo Raw continua disponível.

## Instalação para desenvolvimento

### CPU ou ambiente sem CUDA

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### GPU NVIDIA

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-gpu.txt
```

Para habilitar os modos com LLM:

```powershell
ollama pull qwen2.5:7b-instruct-q5_K_M
```

## Executar

```powershell
python -m sussurro
```

Também é possível usar `Sussurro (dev).bat` após criar o `.venv`.

Por padrão, a configuração atual abre o Sussurro **ativo e pronto para ditar**. Em Ajustes, desative **“Já abrir ativo”** se preferir iniciar em espera para economizar memória.

## Uso

1. Segure `Ctrl+Win` ou o botão do mouse configurado.
2. Fale.
3. Solte o atalho.
4. O HUD informa o estágio de processamento.
5. O texto é colado na janela que estava em foco.

O modo **Raw** usa apenas a transcrição/pós-processamento local. Modos que usam IA precisam do Ollama e do modelo configurado.

> No Windows, um processo sem elevação não pode injetar entrada em uma janela executada como Administrador. Nesse caso, a colagem pode ser bloqueada por UIPI.

## Validação

Instale as dependências de desenvolvimento:

```powershell
pip install -r requirements-dev.txt
```

Execute a suíte rápida:

```powershell
python scripts\validate_all.py
```

Ou rode as etapas separadamente:

```powershell
ruff check sussurro scripts tests
pytest
python scripts\check_imports.py
```

Smoke tests que dependem de hardware/modelos:

```powershell
python scripts\verify_gpu.py
python scripts\smoke.py
```

## Estrutura

```text
Sussurro/
├─ sussurro/              # aplicação
│  ├─ asr/                # Whisper e pós-processamento
│  ├─ audio/              # captura do microfone
│  ├─ hotkey/             # teclado/mouse global
│  ├─ inject/             # colagem/digitação
│  ├─ llm/                # Ollama e modos
│  ├─ storage/            # config, histórico e dicionário
│  ├─ ui/                 # PySide6, HUD, tray e telas
│  └─ assets/             # imagens versionáveis
├─ tests/                 # testes automatizados
├─ scripts/               # diagnóstico e smoke tests
├─ docs/                  # arquitetura, auditoria e design
├─ installer/             # Inno Setup
├─ .github/workflows/     # CI
├─ requirements.txt       # runtime base/CPU
├─ requirements-gpu.txt   # runtime + CUDA NVIDIA
├─ requirements-dev.txt   # testes/lint/build
└─ sussurro.spec          # PyInstaller
```

A arquitetura detalhada está em [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Build do instalador

Consulte [`installer/README.md`](installer/README.md).

## Dados e privacidade

Os dados do usuário ficam em `%APPDATA%\Sussurro`. O histórico não é enviado pelo Sussurro para um serviço remoto. O cliente de LLM fala com o Ollama em `127.0.0.1`.

Modelos do Whisper/Hugging Face e do Ollama podem exigir download inicial. Depois de disponíveis localmente, o fluxo de transcrição/refinamento não depende de uma API de nuvem do projeto.

## Segurança

Consulte [`SECURITY.md`](SECURITY.md). Não publique tokens, dumps de `%APPDATA%`, modelos, `.env` ou logs com dados pessoais em issues.

## Contribuição

Consulte [`CONTRIBUTING.md`](CONTRIBUTING.md) antes de abrir um pull request.

## Licença

Distribuído sob a **MIT License**. Consulte [`LICENSE`](LICENSE) para os termos completos.
