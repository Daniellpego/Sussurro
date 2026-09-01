# Arquitetura do Sussurro

Este documento descreve a arquitetura **implementada e em produção** no repositório atual. O plano histórico original foi preservado em [`docs/legacy/INITIAL_PLAN.md`](./legacy/INITIAL_PLAN.md) apenas como referência e não deve ser tratado como especificação vigente.

---

## 1. Visão Geral

O **SUSURRO** é uma aplicação desktop nativa para Windows (10 e 11) desenvolvida com arquitetura *local-first*, modular e orientada a baixa latência. Ele opera de forma não intrusiva na bandeja do sistema (*System Tray*), capturando voz via *Push-to-Talk* global, transcrevendo em tempo real com `faster-whisper` (Whisper Large-v3-Turbo / CTranslate2), aplicando pós-processamento determinístico de português e comandos de voz, passando opcionalmente por refinamento local via Ollama (Qwen 2.5), e injetando o texto final diretamente no aplicativo em foco via Windows API (Win32).

```text
       +-------------------------------------------------------------+
       |                  Global Input Listener                      |
       |     pynput: Teclado (Ctrl+Win) / Mouse (Botão Lateral)      |
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |                  Audio Capture Pipeline                     |
       |        sounddevice: 16 kHz Mono Float32 Ring Buffer         |
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |                  ASR Transcription Worker                   |
       |  faster-whisper (Large-v3-Turbo / Small / Medium)           |
       |  Aceleração: CUDA FP16 (com auto fallback gracioso pra CPU) |
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |                  Deterministic Postprocess                  |
       |  - Normalização de pontuação e capitalização semântica      |
       |  - Comandos de voz (novo parágrafo, vírgula, interrogação)  |
       |  - Dicionário do Usuário (substituições literais)           |
       |  - Dicionários Especializados (Jurídico, Médico, Dev)       |
       |  - Expansão de Macros PT-BR (CPF, CNPJ, Processo, etc.)     |
       +------------------------------+------------------------------+
                                      |
                         +------------+------------+
                         |                         |
               Modo Raw? |                         | Modos Inteligentes
                         v                         v (Clean, Formal, etc.)
       +------------------------------+  +---------------------------+
       |         Direto para          |  |     Local LLM Worker      |
       |        Armazenamento         |  |   Ollama HTTP API         |
       |         e Injeção            |  |   Qwen 2.5 (VRAM isolada) |
       +--------------+---------------+  +-------------+-------------+
                      |                                |
                      +----------------+---------------+
                                       |
                                       v
       +-------------------------------------------------------------+
       |                   Storage & History Layer                   |
       |     history.json (Append-only FIFO com rotação de 500)      |
       |     config.toml  (Escrita atômica segura)                   |
       |     modes.json   (Presets e prompts customizáveis)          |
       +-------------------------------+-----------------------------+
                                       |
                                       v
       +-------------------------------------------------------------+
       |                     Win32 Paste Engine                      |
       |  1. Salva estado anterior da Área de Transferência          |
       |  2. Injeta texto via Clipboard API + Sintetização Ctrl+V    |
       |  3. Fallback de compatibilidade: Shift+Insert / SendInput   |
       |  4. Restaura estado original do Clipboard com debounce      |
       +-------------------------------------------------------------+
```

---

## 2. Módulos do Sistema

### 2.1 Orquestração Central (`sussurro/app.py`)
- Ponto de entrada do runtime Qt. Inicializa o `QApplication`, carrega temas, orquestra janelas (Configurações, Onboarding, Histórico, Modos), instancia o HUD flutuante (`FloatingHUD`), registra os listeners de atalhos globais e gerencia o ciclo de vida dos workers em segundo plano (`WhisperWorker`, `LLMWorker`).
- Gerencia a política de economia inteligente de VRAM (`smart_economy` e `unload_idle`), descarregando modelos ociosos sem interferir em outras instâncias do Ollama.

### 2.2 Captura de Áudio (`sussurro/audio/`)
- `audio/capture.py`: Gerencia streams do `sounddevice` em 16.000 Hz mono com cálculo de RMS em tempo real para alimentação do indicador visual de volume do HUD.
- Possui resiliência contra desconexão de dispositivos e recuperação graciosa de falhas de hardware de áudio.

### 2.3 Reconhecimento de Voz (`sussurro/asr/`)
- `asr/whisper.py`: Carrega e executa instâncias do `faster-whisper.WhisperModel`. Suporta os modelos `large-v3-turbo` (padrão de alta precisão), `large-v3`, `medium`, `small`, `base` e `tiny`.
- Implementa detecção automática de hardware com aceleração CUDA FP16/INT8 e fallback transparente para CPU (`int8`) caso CUDA/cuDNN não estejam presentes.
- `asr/postprocess.py`: Motor determinístico de formatação textual:
  - Capitalização de início de frases e pós-pontuação.
  - Reconhecimento e conversão de comandos de voz em pontuação real (`vírgula`, `ponto final`, `novo parágrafo`, `ponto de interrogação`, `dois pontos`).
  - Dicionário fonético e termos personalizados.
  - Expansão de macros com padrões regex (ex: formatação de números de processos, CPF, datas e termos técnicos).

### 2.4 Integração LLM Local (`sussurro/llm/`)
- `llm/ollama.py`: Cliente HTTP síncrono/assíncrono para o daemon do Ollama em `http://127.0.0.1:11434`.
- `llm/modes.py`: Gerenciamento de modos de escrita (`Raw`, `Clean`, `Formal`, `Resumo`, `Bullet Points`, `Traduzir EN`, `Traduzir ES`). Permite ao usuário criar modos personalizados com prompts customizados.
- `llm/worker.py`: `QThread` assíncrona para processamento sem bloqueio da interface do usuário.
- Mecanismo de isolamento: as funções `unload_models` e `unload_model` descarregam exclusivamente os modelos registrados pelo Sussurro (`qwen2.5:*`), prevenindo o descarregamento inadvertido de modelos externos do usuário.

### 2.5 Injeção de Texto no Windows (`sussurro/inject/`)
- `inject/paste.py`: Injeção não intrusiva de texto no aplicativo ativo do Windows.
- Preserva a janela em foco antes da gravação através de chamadas Win32 (`GetForegroundWindow` / `SetForegroundWindow`).
- Estratégia em camadas:
  1. Transferência atômica para o clipboard do Windows + emissão de `Ctrl+V` sintetizado via `SendInput`.
  2. Fallback para `Shift+Insert` (para terminais e prompts de comando).
  3. Fallback para injeção caractere-a-caractere via `SendInput` com suporte completo a UTF-16 / surrogate pairs (emojis e caracteres especiais).
  4. Restauração do clipboard original com proteção contra race conditions.

### 2.6 Camada de Armazenamento e Persistência (`sussurro/storage/`)
- Localização padrão: `%APPDATA%\Sussurro` (resolvido dinamicamente via `storage/paths.py`).
- `storage/config.py`: Configurações salvas em formato TOML com validação de esquema e escrita atômica.
- `storage/history.py`: Histórico local append-only com rotação FIFO (máximo 500 entradas), serializado em JSON formatado.
- `storage/dictionary.py`: Dicionário customizado e regras de substituição de termos.
- `storage/autostart.py`: Integração com o Registro do Windows (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).

### 2.7 Interface do Usuário (`sussurro/ui/`)
- Desenvolvida em PySide6/Qt com tema moderno (*Dark/Light mode*), paleta cromática sofisticada e componentes sem bordas com cantos arredondados e suporte a DWM / Windows 11 Mica/Acrylic.
- `ui/window.py`: Janela principal de configurações e controle de dispositivos.
- `ui/overlay.py`: HUD flutuante translúcido com indicação de estado (*Ouvindo*, *Transcrevendo*, *Refinando*, *Concluído*).
- `ui/history_ui.py`: Dashboard completo de histórico com busca em tempo real, agrupamento por data (*Hoje*, *Ontem*, *Data*), cópia em um clique com feedback por toast e exclusão seletiva.
- `ui/modes_ui.py`: Editor visual de modos e prompts de sistema do LLM.
- `ui/setup_ui.py` & `setup_check.py`: Assistente de configuração inicial com detecção de hardware, download com barra de progresso do Whisper e do Ollama.

---

## 3. Empacotamento e Distribuição

O pipeline de build é configurado para gerar duas variantes independentes e autocontidas:

1. **Variante CPU (`SussurroSetup-CPU.exe`):**
   - Binário PyInstaller de ~440 MB compactado via Inno Setup (LZMA2/Max) em instalador de ~110 MB.
   - Ideal para qualquer notebook ou computador Windows 10/11 sem GPU dedicada.
2. **Variante CUDA (`SussurroSetup-CUDA.exe`):**
   - Binário PyInstaller de ~940 MB incluindo DLLs de runtime NVIDIA cuBLAS 12 e cuDNN 9, compactado em instalador de ~1.0 GB.
   - Execução ultra-rápida em placas de vídeo NVIDIA GeForce RTX / GTX.
