# Licenças e Atribuições de Terceiros (Third-Party Licenses)

O **SUSURRO** é distribuído sob a Licença MIT (Copyright (c) 2026 Susurro Oficial).
Esta aplicação incorpora, empacota ou interage com as seguintes tecnologias e bibliotecas de código aberto:

---

## 1. Faster-Whisper & CTranslate2
- **Autor / Mantenedor:** Guillaume Klein, Systran, OpenNMT
- **Licença:** MIT License
- **Descrição:** Motor de inferência rápida em C++ para o modelo Whisper com quantização INT8 e aceleração FP16/CUDA.

---

## 2. PySide6 (Qt for Python)
- **Autor / Mantenedor:** The Qt Company
- **Licença:** GNU Lesser General Public License v3 (LGPLv3) / Commercial
- **Descrição:** Framework de interface gráfica nativa para desktop Windows. O Sussurro interage dinamicamente com as bibliotecas Qt sem modificação do código-fonte do Qt.

---

## 3. Ollama
- **Autor / Mantenedor:** Ollama Inc.
- **Licença:** MIT License
- **Descrição:** Servidor local de inferência de Large Language Models (LLM).

---

## 4. Qwen 2.5 (Pesos GGUF)
- **Autor / Mantenedor:** Alibaba Cloud / Qwen Team
- **Licença:** Apache 2.0 / Qwen Community License
- **Descrição:** Modelo de linguagem local utilizado para os presets de reescrita, pontuação e sumarização de texto.

---

## 5. Bibliotecas de Áudio e Sistema (Python)
- **sounddevice & PortAudio:** MIT License / PortAudio License (captura de áudio em tempo real com baixa latência).
- **soundfile & libsndfile:** MIT License / LGPL (leitura e gravação de arquivos de áudio).
- **NumPy:** BSD 3-Clause License (processamento e cálculo RMS de arrays de áudio).
- **pyperclip:** BSD 3-Clause License (integração multiplataforma com área de transferência).
- **pynput:** GNU LGPLv3 (monitoramento global de eventos de teclado e mouse).
- **keyboard:** MIT License (injeção e atalhos de teclado de baixo nível no Windows).
- **httpx:** BSD 3-Clause License (cliente HTTP assíncrono e síncrono para comunicação local com Ollama).
- **huggingface-hub:** Apache 2.0 License (download e gerenciamento de cache de modelos ASR).
- **tomli & tomli-w:** MIT License (leitura e escrita atômica de arquivos de configuração TOML).

---

## 6. NVIDIA CUDA Runtime & cuDNN (Variante GPU)
- **Autor / Mantenedor:** NVIDIA Corporation
- **Licença:** NVIDIA Software License Agreement (Redistributable Runtime Libraries)
- **Descrição:** DLLs redistribuíveis do runtime CUDA 12 e cuBLAS/cuDNN empacotadas na variante GPU para aceleração por hardware em GPUs NVIDIA GeForce / RTX.
