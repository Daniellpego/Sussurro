# Sussurro — Wispr/SuperWhisper local, gratuito, offline

> **Objetivo**: alternativa local 100% gratuita ao Wispr Flow / SuperWhisper.
> Push-to-talk no PC, transcreve a fala (PT-BR + EN code-switching), passa
> por um LLM local pra "limpar / reescrever / traduzir" conforme o modo
> selecionado, e cola o resultado no app ativo.

---

## 1. Hardware-alvo (confirmado)

- **GPU**: RTX 4070 Ti (12 GB VRAM)
- **RAM**: 32 GB
- **CPU**: Ryzen 7 5800X3D
- **OS**: Windows 11

Esse perfil permite Whisper + LLM 7B residentes em VRAM simultaneamente.
Latência-alvo end-to-end: **~500 ms transcrição + ~1-2 s reescrita LLM**.

---

## 2. Stack escolhida

| Camada | Escolha | Por quê |
|---|---|---|
| Linguagem | Python 3.11 | Ecossistema maduro pra áudio + ML local no Windows. |
| ASR | `faster-whisper` + `large-v3` (int8_float16) | Qualidade máxima em PT-BR coloquial, code-switching PT/EN, pontuação rica que reflete tom. ~3 GB VRAM, ainda rápido que tempo real na 4070 Ti. |
| VAD | Silero VAD (via `silero-vad` package) | Detecção de fim-de-fala robusta, leve, sem dependência de torch hub. |
| Captura áudio | `sounddevice` (PortAudio) | API simples, baixa latência, multiplataforma. |
| LLM local | Ollama + `qwen2.5:7b-instruct-q5_K_M` | Melhor 7B em PT-BR pra gíria + code-switching. ~5.5 GB VRAM. Plano B: `llama3.1:8b-instruct-q5_K_M`. |
| Hotkey global | `pynput` (com fallback Win32 `RegisterHotKey` via pywin32) | `pynput` é mais portável; pywin32 é o "plano B" quando há app elevado. |
| Clipboard / paste | `pyperclip` + `keyboard.send('ctrl+v')` | Funciona em ~95% dos apps; fallback: digitar via SendInput. |
| UI overlay | **PySide6** (Qt) com QSS + frameless transparente | Pílula flutuante estilo Wispr Flow: vidro escuro, cantos arredondados, animação de waveform, fade in/out suave. Performance nativa, controle total de estilo. |
| UI tray | `pystray` + `Pillow` | Ícone na bandeja com troca de modo, complementa o overlay. |
| Configuração | TOML via `tomli`/`tomli-w` | Editável à mão, sem boilerplate. |
| Empacotamento | venv + `requirements.txt` (PyInstaller só se quiser .exe) | Simples; .exe é otimização posterior. |

---

## 3. Arquitetura (high-level)

```
+----------------+    audio bytes    +-----------------+
|  Mic capture   |------------------>|   VAD + buffer  |
|  sounddevice   |  16kHz mono       |   (Silero VAD)  |
+----------------+                   +--------+--------+
        ^                                     |
        | start/stop                          | utterance WAV
        |                                     v
+----------------+                   +-----------------+
| Hotkey daemon  |---trigger-------->|  faster-whisper |
|  (pynput)      |                   |  large-v3-turbo |
+----------------+                   +--------+--------+
        |                                     |
        | mode switch                         | raw text
        v                                     v
+----------------+                   +-----------------+
| Tray UI        |---current mode--->|  Mode router    |
| (pystray)      |                   |  (Ollama LLM)   |
+----------------+                   +--------+--------+
                                              |
                                              | final text
                                              v
                                     +-----------------+
                                     |  Clipboard +    |
                                     |  paste injector |
                                     +-----------------+
```

Componente central: um **event loop async** que cola tudo. Fila de
áudio → fila de transcrição → fila de pós-processamento → injector.

---

## 4. Modos (o que diferencia de "Whisper cru")

Modos são prompts pré-definidos aplicados pelo LLM. Trocados via tray
ou hotkey (`Ctrl+Alt+1..7`):

| # | Modo | O que faz |
|---|---|---|
| 1 | **Raw** | Transcrição direta, sem LLM. Mais rápido. |
| 2 | **Clean** | Remove "é", "tipo", "uhm", corrige gramática, mantém o tom. |
| 3 | **Email** | Reescreve em tom profissional, estrutura em parágrafos. |
| 4 | **Bullets** | Transforma divagação em bullets organizados. |
| 5 | **Prompt** | Transforma fala natural em um prompt limpo pra outro LLM. |
| 6 | **Code** | Identifica código falado, formata em snake_case/camelCase, blocos. |
| 7 | **Translate EN** | Fala em PT-BR, saída em inglês. |

Prompts ficam em `config/modes.toml` — editáveis sem código.

---

## 5. Fases de construção

Cada fase entrega algo testável. Commit ao fim de cada uma.

### Phase 0 — Setup & smoke test (1 h)
**Done quando**: `python smoke.py audio.wav` imprime transcrição correta.

- [ ] `python -m venv .venv` + ativar
- [ ] `requirements.txt` inicial (faster-whisper, sounddevice, numpy)
- [ ] CUDA + cuDNN (verificar `nvidia-smi`, baixar runtime se faltar)
- [ ] Script `smoke.py` que carrega `large-v3-turbo` e transcreve um .wav
- [ ] Medir: tempo de warm-up + tempo de inferência em 10 s de áudio
- [ ] Commit: `chore: phase 0 — environment + faster-whisper smoke test`

**Riscos**: cuDNN ausente é o tropeço mais comum no Windows. Tem mitigação
documentada na issue do faster-whisper (binários pré-compilados).

### Phase 1 — Push-to-talk + overlay bonito → clipboard (5-6 h)
**Done quando**: segurar hotkey → overlay flutuante aparece com waveform animado → soltar → spinner "transcrevendo" → texto cola no app ativo → overlay some com fade.

**Visual** (estilo Wispr Flow / Raycast):
- Pílula flutuante 360×64 px, centrada no rodapé da tela (~80 px do bottom)
- Frameless, sempre-no-topo, background translúcido escuro com cantos bem arredondados (24 px)
- Waveform animado em tempo real durante gravação (barras refletindo nível RMS)
- Spinner + texto "transcrevendo..." durante inferência
- Fade in 150 ms / fade out 200 ms
- Indicador de modo: chip colorido no canto esquerdo (default = "Raw")
- Fonte: Inter ou Segoe UI Variable, branco com 90% opacidade

**Funcional**:
- [ ] Captura de áudio assíncrona (sounddevice InputStream, 16 kHz mono)
- [ ] Buffer in-memory + flush em release
- [ ] Hotkey global push-to-talk (default: `Ctrl+Win+Espaço`, configurável)
- [ ] Pre-load do modelo no startup (warm-up com áudio de 1s silêncio)
- [ ] Pipeline: release → numpy buffer → transcribe → clipboard → Ctrl+V
- [ ] Worker thread pro Whisper (UI nunca trava)
- [ ] Commit: `feat: phase 1 — push-to-talk + floating overlay UI`

**Riscos**:
- Hotkey pode falhar em janelas elevadas → fallback pywin32.
- Paste falha em alguns terminais → fallback "digitar via SendInput" como modo.
- Frameless + always-on-top no Windows precisa de flags Qt corretas (`Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint`) — testado, funciona.

### Phase 2 — Modos + LLM local (3-4 h)
**Done quando**: trocar modo via hotkey troca o pós-processamento; "Clean" remove "é" e fillers.

- [ ] Instalar Ollama + puxar `qwen2.5:7b-instruct-q4_K_M`
- [ ] `OLLAMA_KEEP_ALIVE=24h` pra modelo ficar quente
- [ ] `config/modes.toml` com prompts iniciais dos 7 modos
- [ ] Mode router: lê modo atual, chama Ollama via HTTP (`/api/generate`)
- [ ] Streaming da resposta do LLM (typing-effect opcional)
- [ ] Hotkeys de troca: `Ctrl+Alt+1..7`
- [ ] Tray icon mostra modo atual (ícone colorido por modo)
- [ ] Commit: `feat: phase 2 — LLM modes (clean, email, bullets, prompt, code, translate)`

**Riscos**:
- LLM reescreve demais → calibrar prompts (instrução clara: "preserve o significado, não invente").
- VRAM apertada se modelo Whisper crescer → degradar pra `large-v3` int8.

### Phase 3 — Polish & DX (2-3 h)
**Done quando**: você usa de verdade no dia-a-dia sem irritar.

- [ ] System tray com menu: trocar modo, abrir config, pausar, sair
- [ ] `config/settings.toml`: device de mic, hotkeys, modelo padrão, modo padrão, idioma
- [ ] Auto-start no logon (Windows Startup folder)
- [ ] Logs em `%APPDATA%\sussurro\sussurro.log` (rotacional)
- [ ] Tratamento gracioso de erro (mic desconectado, Ollama offline)
- [ ] Commit: `feat: phase 3 — tray UI, config, autostart, logging`

### Phase 4 — Extras opcionais
Só faz se as fases 1-3 já estiverem usáveis.

- [ ] **VAD auto-stop**: dispensa segurar tecla, para sozinho ao detectar silêncio
- [ ] **Live transcription overlay**: janelinha translúcida mostrando texto em tempo real
- [ ] **Dicionário custom**: palavras técnicas / nomes próprios (initial_prompt)
- [ ] **Hotword**: "ei sussurro" pra ativar sem hotkey (com openWakeWord)
- [ ] **Histórico**: últimas N transcrições recuperáveis via hotkey

---

## 6. Decisões travadas

| # | Decisão | Escolha final |
|---|---|---|
| 1 | Nome do projeto | **Sussurro** |
| 2 | Hotkey push-to-talk | **Ctrl+Win+Espaço** |
| 3 | Modelo Whisper | **`large-v3` full**, quantização `int8_float16` (qualidade > velocidade) |
| 4 | LLM | **Qwen 2.5 7B Q5_K_M** via Ollama |
| 5 | Injeção default | **Paste (Ctrl+V)**, com flag por-app pra forçar typing como fallback |
| 6 | Prompts dos modos | **Emotion-aware**: instrução explícita pra preservar tom, manter termos em inglês quando o falante usou em inglês, não traduzir jargão técnico |

---

## 7. Estrutura inicial de pastas

```
E:\dlp whipser\
├── PLAN.md                     (este arquivo)
├── README.md
├── requirements.txt
├── .gitignore
├── pyproject.toml
├── sussurro\
│   ├── __init__.py
│   ├── __main__.py             (entry point: python -m sussurro)
│   ├── audio\
│   │   ├── capture.py          (sounddevice wrapper)
│   │   └── vad.py              (Silero VAD)
│   ├── asr\
│   │   └── whisper.py          (faster-whisper wrapper)
│   ├── llm\
│   │   ├── ollama_client.py
│   │   └── modes.py            (carrega modes.toml, aplica prompts)
│   ├── inject\
│   │   ├── clipboard.py
│   │   └── keyboard.py         (SendInput fallback)
│   ├── hotkey\
│   │   └── manager.py          (pynput + win32 fallback)
│   ├── ui\
│   │   └── tray.py             (pystray)
│   ├── config.py
│   └── app.py                  (orquestrador, event loop)
├── config\
│   ├── settings.toml
│   └── modes.toml
└── scripts\
    └── smoke.py                (Phase 0 smoke test)
```

---

## 8. Próximo passo

Se você confirmar as decisões da seção 6, eu começo a **Phase 0**:
crio `requirements.txt`, `.gitignore`, `smoke.py` e a gente valida que o
faster-whisper roda na sua 4070 Ti antes de qualquer outra coisa. Esse é
o único ponto que pode dar trabalho de configuração (cuDNN), então quero
validar primeiro pra não construir em cima de areia.
