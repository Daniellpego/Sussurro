# Arquitetura do Instalador Unificado One-Click (SUSURRO + Ollama)

**Data do documento:** 2026-08-31  
**Status:** Planejamento Arquitetural (Bloco E do Roadmap)  
**Autor:** Engenheiro de Software Sênior / Auditor de Repositórios

---

## 1. Visão Geral e Objetivos

O objetivo do instalador *One-Click* é permitir que qualquer usuário no Windows instale e configure o SUSURRO sem necessidade de linha de comando, instalação manual de Python, CUDA, Git ou Ollama. O executável instalador entrega uma experiência pronta para uso (*out-of-the-box*) com aceleração por hardware e LLM local.

---

## 2. Componentes e Estratégia de Empacotamento

A solução é composta por 4 camadas de software:

```
+-------------------------------------------------------------------+
|                        SUSURRO GUI & Core                         |
|  (Executável PyInstaller / Standalone com PySide6 + Dependências)  |
+-------------------------------------------------------------------+
|                    Engine ASR (faster-whisper)                    |
|   (CTranslate2 + DLLs CUDA 12.x / cuDNN v9 + whisper-large-v3-turbo)|
+-------------------------------------------------------------------+
|                    Engine LLM Local (Ollama)                      |
|       (Binários ollama.exe / serviço local + pesos Qwen 2.5)       |
+-------------------------------------------------------------------+
|                    Sistema Operacional (Win32)                    |
|  (Inno Setup / NSIS + Registro de Startup + Atalhos de Bandeja)   |
+-------------------------------------------------------------------+
```

### Componentes detalhados:
1. **SUSURRO Core:**
   * Binário gerado via PyInstaller (`sussurro.spec`) contendo o interpretador Python 3.11 embedado, PySide6, sounddevice, pyperclip e hotkeys.
2. **ASR Runtime (faster-whisper / CTranslate2):**
   * DLLs essenciais de CUDA (`cublas64_12.dll`, `cudnn64_9.dll`, etc.) carregadas via `sussurro/cuda_setup.py`.
   * Pesos do modelo `whisper-large-v3-turbo` quantizado em INT8 (~800 MB).
3. **Ollama Daemon & LLM Local:**
   * Executável nativo `ollama.exe` (distribuível para Windows x64).
   * Pesos do modelo `qwen2.5:7b-instruct-q4_K_M` (~4.7 GB) ou variante compacta `qwen2.5:3b-instruct-q4_K_M` (~1.9 GB).
4. **Instalador Inno Setup (`installer/sussurro.iss`):**
   * Interface gráfica limpa em português.
   * Criação de atalhos no Menu Iniciar e Desktop.
   * Registro opcional de autostart em `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.

---

## 3. Comparativo de Estratégias de Distribuição

| Aspecto | Estratégia A: Híbrida (Slim + On-Demand) | Estratégia B: Full Standalone (Offline) |
|---|---|---|
| **Tamanho do Instalador** | ~180 MB a 220 MB | ~5.8 GB |
| **Download Inicial** | Rápido (< 1 minuto em banda larga comum) | Lento (~10 a 30 minutos) |
| **Primeiro Uso** | Baixa Qwen 2.5 e Whisper com barra de progresso no wizard de setup | 100% imediato e offline |
| **Ambientes sem Internet** | Incompatível sem pre-cache manual | Ideal para ambientes corporativos/médicos isolados |
| **Recomendação** | **Padrão recomendado para lançamento público** | **Opção secundária corporativa/offline** |

---

## 4. Análise de Licenciamento e Riscos Jurídicos

| Software | Licença | Termos de Redistribuição | Risco / Conformidade |
|---|---|---|---|
| **SUSURRO** | MIT License | Copyright (c) 2026 Susurro Oficial | Totalmente livre |
| **Ollama** | MIT License | Permite redistribuição comercial e não-comercial, com inclusão do aviso de copyright | Baixo risco; basta manter o arquivo `LICENSE` do Ollama no pacote |
| **CTranslate2 / Faster-Whisper** | MIT License | Permite redistribuição de binários e bibliotecas | Baixo risco |
| **Qwen 2.5 (Pesos GGUF)** | Apache 2.0 / Qwen Community License | Permite uso comercial e redistribuição gratuita de pesos/quantizações | Baixo risco; requer atribuição padrão da Alibaba Cloud / Qwen |
| **NVIDIA CUDA / cuDNN DLLs** | NVIDIA EULA (Redistributable) | Permite redistribuição de DLLs de runtime (`cudnn`, `cublas`) junto à aplicação | Totalmente compatível |

---

## 5. Roteiro Técnico para a Próxima Rodada (Implementação)

1. **Automação do Build no CI (`.github/workflows/release.yml`):**
   * Script para download dos binários oficiais estáveis do Ollama Windows.
   * Execução do PyInstaller com flags `-w -F` ou diretório `--onedir`.
2. **Compilação Inno Setup via CLI:**
   * `ISCC.exe installer/sussurro.iss /DAppVersion=1.0.0 /O"installer/out"`
3. **Validação de Inicialização Segura:**
   * Garantia de que o processo `ollama.exe` roda isolado na porta local `11434` sem conflitar com instâncias prévias do usuário.
