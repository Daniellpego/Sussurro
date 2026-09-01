# Arquitetura

O Sussurro é uma aplicação de bandeja para Windows. A interface usa PySide6, enquanto a captura global de teclado e mouse e a colagem de texto usam integrações específicas do Windows.

## Fluxo de uma transcrição

1. `hotkey/` detecta quando o atalho de push-to-talk é pressionado.
2. `audio/` captura áudio mono a 16 kHz enquanto o atalho permanece ativo.
3. `asr/whisper.py` envia o áudio ao `faster-whisper`. A seleção de dispositivo tenta CUDA quando configurado e volta para CPU se a inicialização falhar.
4. `asr/postprocess.py` aplica comandos de pontuação, capitalização, substituições do dicionário e macros em português.
5. Nos modos que usam revisão, `llm/` envia o texto ao Ollama local. O modo raw ignora essa etapa.
6. `storage/` grava o histórico e `inject/paste.py` cola o resultado na janela que estava ativa.
7. `ui/overlay.py` acompanha o fluxo com os estados de captura, transcrição e revisão.

## Módulos

### Aplicação e interface

`sussurro/app.py` cria a aplicação Qt, conecta os serviços e controla o encerramento. `sussurro/ui/` contém a janela principal, o menu da bandeja, o overlay, o onboarding e os componentes visuais reutilizáveis.

Trabalho pesado não deve bloquear a thread da interface. Transcrição e revisão são executadas fora dela e retornam o resultado por sinais do Qt.

### Entrada de áudio

`sussurro/audio/capture.py` encapsula o stream do `sounddevice` e entrega amostras `float32` ao pipeline. Os listeners globais ficam em `sussurro/hotkey/` e só controlam o início e o fim da captura.

### Reconhecimento e pós-processamento

`sussurro/asr/whisper.py` concentra carregamento de modelo, escolha de compute type e transcrição. O pós-processamento determinístico fica separado em `sussurro/asr/postprocess.py`, o que permite testá-lo sem carregar um modelo.

### Revisão local

`sussurro/llm/ollama.py` é o cliente HTTP do Ollama em `127.0.0.1`. `modes.py` mantém os modos disponíveis e `worker.py` executa a revisão. O Sussurro só descarrega modelos que ele próprio gerencia.

### Persistência

Configurações, modos, dicionário e histórico ficam em `%APPDATA%\Sussurro`. Escritas que substituem um arquivo usam um arquivo temporário no mesmo diretório e uma troca atômica. O histórico mantém no máximo 500 entradas.

### Injeção de texto

`sussurro/inject/paste.py` preserva a área de transferência, cola o texto por APIs Win32 e restaura o conteúdo anterior. O módulo trata texto UTF-16, inclusive caracteres fora do plano multilíngue básico.

## Empacotamento

`sussurro.spec` gera o bundle com PyInstaller. `installer/sussurro.iss` produz instaladores separados para CPU e CUDA. Tags `v*` acionam `.github/workflows/release.yml`, que cria as duas variantes e publica os checksums SHA-256 junto dos executáveis.

## Testes

Os testes em `tests/` cobrem o pós-processamento, armazenamento, áudio, modos locais, instalação e fallback de hardware. Integrações com microfone, atalhos globais, GPU e foco de janela também precisam de verificação manual no Windows.
