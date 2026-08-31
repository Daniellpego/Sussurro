# Arquitetura do Sussurro

Este documento descreve a arquitetura **implementada** no repositório atual. O plano histórico original foi preservado em [`docs/legacy/INITIAL_PLAN.md`](./legacy/INITIAL_PLAN.md) apenas como referência e não deve ser tratado como especificação vigente.

## Visão geral

O Sussurro é um aplicativo desktop para Windows escrito em Python. O processo fica residente na bandeja do sistema e coordena captura de áudio, transcrição local, pós-processamento opcional por LLM local e colagem do texto na janela que estava em foco.

```text
Hotkey / botão do mouse
        |
        v
+-------------------+      +--------------------+
| audio.capture     | ---> | asr.whisper        |
| sounddevice       |      | faster-whisper     |
+-------------------+      +---------+----------+
                                    |
                                    v
                           +--------------------+
                           | postprocess +      |
                           | comandos de voz    |
                           +---------+----------+
                                     |
                          modo Raw?  |  não
                            +--------+---------+
                            |                  |
                            v                  v
                     texto final      +----------------+
                                      | llm.worker     |
                                      | Ollama local   |
                                      +--------+-------+
                                               |
                                               v
                                        texto refinado
                                               |
                                               v
                                     +------------------+
                                     | inject.paste     |
                                     | clipboard/Win32  |
                                     +------------------+
```

## Módulos

### `sussurro/app.py`
Orquestrador da aplicação. Cria a aplicação Qt, janela principal, HUD, tray, listeners, recorder, worker ASR e worker LLM. Também coordena pausa/ativação, ciclo de vida e persistência de histórico.

### `sussurro/audio/`
Captura de microfone em 16 kHz mono com `sounddevice`. Mantém buffer do push-to-talk e nível RMS para feedback visual.

### `sussurro/asr/`
Worker de transcrição baseado em `faster-whisper`. Implementa fallback de CUDA para CPU e pós-processamento determinístico da transcrição.

### `sussurro/hotkey/`
Listeners globais via `pynput` para `Ctrl+Win` e botão de mouse configurável.

### `sussurro/inject/`
Colagem robusta no aplicativo em foco. Tenta clipboard + `Ctrl+V`, `Shift+Insert` e digitação Unicode por Win32 conforme configuração/fallback.

### `sussurro/llm/`
Integração opcional com Ollama em `localhost`. `modes.py` mantém modos editáveis persistidos em JSON; `worker.py` processa jobs fora da thread de UI.

### `sussurro/storage/`
Configuração TOML, histórico JSON, dicionário do usuário, caminhos `%APPDATA%` e autostart no Registro do Windows. Escritas críticas usam substituição atômica.

### `sussurro/ui/`
Interface PySide6/Qt: janela principal, HUD, onboarding, histórico, ajustes, editor de modos, tray e kit de componentes reutilizáveis. O tema é centralizado em `ui/theme.py`.

### `scripts/`
Ferramentas operacionais e de diagnóstico que não são testes unitários: verificação de imports, smoke ASR/GPU e captura de screenshots.

### `tests/`
Testes automatizados sem necessidade de GPU, microfone real ou Ollama ativo. Cobrem pós-processamento, armazenamento, recorder, integração Ollama, robustez e regras de setup.

### `docs/design/`
Handoff, mockups e referências visuais. Não são executados pela aplicação.

### `installer/`
Definição do instalador Inno Setup e instruções de build. O executável é produzido por PyInstaller a partir de `sussurro.spec`.

## Threads e concorrência

- Thread principal: event loop do Qt e UI.
- Recorder: callback de áudio do `sounddevice`.
- `WhisperWorker`: `QThread` com fila de jobs; mantém o modelo residente enquanto o Sussurro está ativo.
- `LLMWorker`: `QThread` com fila de jobs e chamadas HTTP ao Ollama.
- Listeners `pynput`: threads próprias para teclado e mouse.
- Downloads do primeiro uso: workers Qt separados para não bloquear a UI.

## Dados persistentes

Por padrão, dados do usuário ficam em `%APPDATA%\Sussurro`:

- `config.toml`: configuração;
- `history.json`: histórico local de transcrições;
- `modes.json`: modos e prompts;
- arquivos do dicionário/sugestões.

A desinstalação preserva esses dados. O usuário pode removê-los manualmente se desejar reset completo.

## Rede e privacidade

A transcrição e a reescrita não usam API de nuvem do Sussurro. O Ollama é acessado apenas em `127.0.0.1`. Conexão com a internet pode ser necessária no primeiro uso para baixar modelos do Hugging Face e, se o recurso de IA for habilitado, o modelo do Ollama.

## Plataforma

O alvo oficial é Windows 10/11. Existem integrações específicas com Win32/DWM, bandeja do sistema, Registro e `winsound`. O projeto não declara suporte oficial a macOS ou Linux.

## Empacotamento

1. PyInstaller lê `sussurro.spec` e cria `dist/Sussurro/`.
2. Inno Setup lê `installer/sussurro.iss` e gera `installer/out/SussurroSetup.exe`.
3. Assets opcionais são incluídos apenas quando presentes; a ausência de fontes/sons customizados não deve impedir o build.
