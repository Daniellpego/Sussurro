# SUSURRO

<div align="center">

[![CI Status](https://github.com/Daniellpego/Sussurro/actions/workflows/ci.yml/badge.svg)](https://github.com/Daniellpego/Sussurro/actions/workflows/ci.yml)
[![Latest Release](https://img.shields.io/github/v/release/Daniellpego/Sussurro?color=blue&label=release)](https://github.com/Daniellpego/Sussurro/releases/latest)
[![Python Version](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg?logo=windows&logoColor=white)](https://www.microsoft.com/windows)

**Ditado por voz inteligente, local-first e ultra-rápido para Windows.**  
Pressione uma tecla de atalho global, fale com naturalidade em qualquer aplicativo e tenha seu texto transcrito, pontuado e formatado com perfeição — **100% offline e com privacidade absoluta**.

[Instalação](#-instalação-rápida-instalador-windows) •
[Funcionalidades](#-funcionalidades-principais) •
[Como Usar](#-como-usar) •
[Requisitos de Sistema](#-requisitos-de-sistema) •
[Desenvolvimento](#-desenvolvimento-local) •
[Arquitetura](#-arquitetura)

</div>

---

## ⚡ Por que o Sussurro?

- 🔒 **100% Local e Privado:** Nenhum áudio, histórico ou dado de voz é enviado para a nuvem. Toda a inferência roda diretamente no seu computador.
- ⚡ **Inferência com Whisper Turbo:** Equipado com o modelo de alta velocidade `faster-whisper-large-v3-turbo` (CTranslate2), garantindo transcrições precisas em frações de segundo.
- 🎯 **Integração com Qualquer Aplicativo:** Funciona sobre qualquer janela ativa (Word, WhatsApp Desktop, VS Code, Google Docs, Notion, navegadores, prontuários ou sistemas jurídicos) sem roubar o foco.
- 🧠 **Refinamento com IA Local (Ollama):** Reescreva notas brutas, remova hesitações (*"hã"*, *"ééé"*), estruture em tópicos ou formate termos jurídicos e médicos com o modelo local Qwen 2.5.
- 📦 **Instalador One-Click:** Baixe e execute o instalador padrão do Windows (`.exe`). Sem necessidade de configurar Python, Git ou variáveis de ambiente.

---

## 📥 Instalação Rápida (Instalador Windows)

Baixe a versão mais recente (**v0.1.1**) na página de **[Releases Oficiais](https://github.com/Daniellpego/Sussurro/releases/latest)**:

| Variante | Tamanho | Recomendado Para | Download Oficial (v0.1.1) |
|---|---|---|---|
| **Sussurro CPU** | ~94 MB | Computadores e notebooks sem placa de vídeo dedicada (roda em qualquer processador moderno). | [Baixar `SussurroSetup-CPU.exe`](https://github.com/Daniellpego/Sussurro/releases/download/v0.1.1/SussurroSetup-CPU.exe) |
| **Sussurro CUDA (GPU)** | ~1.05 GB | Computadores equipados com placas de vídeo **NVIDIA GeForce / RTX** (máxima performance). | [Baixar `SussurroSetup-CUDA.exe`](https://github.com/Daniellpego/Sussurro/releases/download/v0.1.1/SussurroSetup-CUDA.exe) |

> Para consultar versões anteriores ou notas de lançamento de todas as versões, acesse o [Histórico de Releases](https://github.com/Daniellpego/Sussurro/releases).

### Verificação de Integridade (SHA-256)
Todos os binários oficiais acompanham o arquivo [`checksums-sha256.txt`](https://github.com/Daniellpego/Sussurro/releases/download/v0.1.1/checksums-sha256.txt) gerado automaticamente pelo GitHub Actions. Para verificar no PowerShell:
```powershell
Get-FileHash SussurroSetup-CPU.exe -Algorithm SHA256
```

---

## ✨ Funcionalidades Principais

### 🎙️ Reconhecimento de Fala de Alta Precisão (ASR)
- Motor `faster-whisper` em C++ com suporte aos modelos `large-v3-turbo`, `large-v3`, `medium` e `small`.
- Fallback automático e gracioso de hardware: se o suporte CUDA não estiver presente, o sistema migra dinamicamente para execução em CPU com quantização INT8.

### ✍️ Pós-Processamento Semântico e Comandos de Voz
- **Pontuação Automática:** Reconhece comandos falados como *"vírgula"*, *"ponto final"*, *"dois pontos"*, *"ponto de interrogação"* e *"novo parágrafo"*.
- **Capitalização Semântica:** Ajusta maiúsculas no início de períodos e após quebras de linha de forma determinística.
- **Dicionário Personalizado:** Adicione termos técnicos, siglas, nomes próprios ou gírias regionais.
- **Macros de Formatação PT-BR:** Expansão e formatação automática de padrões como CPF, CNPJ e números de processos jurídicos.

### 🤖 Presets de IA e Modos Editáveis (Ollama)
Alterne rapidamente o estilo do ditado através do menu da bandeja ou da tela de Modos:
- **Raw:** Transcrição direta e pura do Whisper, ultra-rápida (sem passar pelo LLM).
- **Clean:** Remove repetições, vícios de linguagem e hesitações mantendo a essência do que foi falado.
- **Formal:** Converte a fala coloquial em texto profissional, culto e bem articulado.
- **Resumo:** Sintetiza reuniões ou gravações longas em um resumo conciso.
- **Bullet Points:** Estrutura ideias ditadas em listas organizadas de tópicos.
- **Traduzir (Inglês / Espanhol):** Traduz automaticamente a fala em português para o idioma de destino.
- **Modos Personalizados:** Crie seus próprios estilos com prompts de sistema personalizados no editor integrado.

### 📊 Dashboard de Histórico Integrado
- **Busca em Tempo Real:** Localize instantaneamente qualquer ditado passado enquanto digita.
- **Agrupamento Cronológico:** Visualização organizada por dias (*Hoje*, *Ontem*, *Data*).
- **Cópia em 1 Clique:** Clique em qualquer card de histórico para copiar o texto com feedback visual animado (*toast*).
- **Gestão Segura:** Exclua itens individualmente ou limpe o histórico com confirmação. Rotação FIFO automática das últimas 500 entradas.

### 🪟 HUD Flutuante e Injeção Não Intrusiva
- HUD translúcido com animações de estado (*Ouvindo*, *Transcrevendo*, *Refinando*, *Concluído*) e indicador visual de volume do microfone.
- Injeção inteligente via Win32 API (`SendInput` + Clipboard com preservação do conteúdo anterior e suporte a emojis UTF-16).

---

## 🎮 Como Usar

```text
1. Segure o atalho global:
   [ Ctrl ] + [ Win ]   (ou o botão lateral do mouse configurado)

2. Fale o seu texto com naturalidade...

3. Solte o atalho.
   -> O HUD processa o áudio e cola o resultado diretamente no seu cursor!
```

### Acesso Rápido pela Bandeja do Sistema (*System Tray*)
- **Clique Duplo:** Abre a tela de Configurações / Ajustes.
- **Clique com Botão Direito:** Menu rápido com seleção de Modos, Histórico, Pausar/Retomar e Sair.

---

## 💻 Requisitos de Sistema

| Componente | Requisito Mínimo (Variante CPU) | Recomendado (Variante CUDA) |
|---|---|---|
| **Sistema Operacional** | Windows 10 (Build 19041+) ou Windows 11 | Windows 10 ou Windows 11 (64-bit) |
| **Processador (CPU)** | Intel Core i3 / AMD Ryzen 3 (4 núcleos) | Intel Core i5 / AMD Ryzen 5 ou superior |
| **Memória RAM** | 8 GB RAM | 16 GB RAM |
| **Placa de Vídeo (GPU)** | Não necessária | NVIDIA RTX série 20/30/40 com 6 GB+ VRAM |
| **Espaço em Disco** | 3 GB livres | 8 GB livres (para modelos Whisper + Ollama) |
| **Microfone** | Qualquer microfone USB ou integrado | Microfone com redução de ruído |

---

## 🛠️ Desenvolvimento Local

Caso deseje compilar ou contribuir com o código-fonte:

### 1. Clonar o Repositório e Criar Ambiente Virtual
```powershell
git clone https://github.com/Daniellpego/Sussurro.git
cd Sussurro

# Criar ambiente virtual com Python 3.11+
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar Dependências
```powershell
# Dependências base + desenvolvimento + linters
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

# (Opcional) Para acelerar com GPU NVIDIA:
pip install -r requirements-gpu.txt
```

### 3. Executar o Aplicativo
```powershell
python -m sussurro
```

### 4. Executar Testes e Validação de Qualidade
```powershell
# Linter (Ruff)
ruff check sussurro scripts tests installer

# Validador completo de imports e compilação
python scripts/validate_all.py

# Suíte de testes unitários (pytest)
pytest -v
```

---

## 🏛️ Arquitetura

O projeto segue uma arquitetura em camadas orientada a eventos e isolamento de responsabilidades:

```text
Sussurro/
├── sussurro/
│   ├── app.py                  # Orquestrador central e ciclo de vida Qt
│   ├── asr/                    # faster-whisper, pós-processamento determinístico e macros
│   ├── audio/                  # Captura de microfone com sounddevice e cálculo de RMS
│   ├── hotkey/                 # Listeners globais de teclado (Ctrl+Win) e mouse
│   ├── inject/                 # Injeção de texto Win32 (Clipboard, Shift+Insert, SendInput)
│   ├── llm/                    # Cliente Ollama, editor de modos e isolamento de VRAM
│   ├── storage/                # Persistência atômica de config (TOML), histórico e dicionário
│   ├── ui/                     # Interface PySide6, HUD flutuante, histórico, ajustes e temas
│   └── assets/                 # Ícones e imagens do aplicativo
├── tests/                      # 35 testes automatizados cobrindo todas as camadas
├── scripts/                    # Utilitários de diagnóstico, smoke tests e screenshots
├── docs/                       # Documentação técnica (Arquitetura, Auditoria, Licenças)
├── installer/                  # Scripts Inno Setup 6 parametrizados para CPU e CUDA
└── .github/workflows/          # CI de qualidade e pipeline de release multi-variante
```

Para uma análise detalhada da arquitetura técnica, consulte o documento [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 🔒 Segurança e Privacidade

- **Zero Coleta de Dados:** O Sussurro não possui rastreadores, telemetria invasiva ou conexão com servidores externos do projeto.
- **Armazenamento Local:** Todos os dados de configuração e histórico residem exclusivamente em `%APPDATA%\Sussurro` no seu próprio disco.
- Para diretrizes de divulgação responsável ou reporte de vulnerabilidades, consulte [`SECURITY.md`](SECURITY.md).

---

## 🤝 Como Contribuir

Contribuições são muito bem-vindas! Siga estas etapas:
1. Faça um Fork do projeto.
2. Crie uma branch para sua funcionalidade (`git checkout -b feature/minha-feature`).
3. Certifique-se de que os testes passem (`ruff check` e `pytest`).
4. Envie suas alterações (`git commit -m 'feat: minha nova feature'`).
5. Abra um Pull Request.

Consulte o guia detalhado em [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## 📄 Licença e Atribuições

Distribuído sob a **Licença MIT**. Consulte o arquivo [`LICENSE`](LICENSE) para mais detalhes.  
As atribuições e termos das bibliotecas de terceiros (PySide6, Faster-Whisper, Ollama, Qwen, PortAudio) estão documentadas em [`docs/THIRD_PARTY_LICENSES.md`](docs/THIRD_PARTY_LICENSES.md).
