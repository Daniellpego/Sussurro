# Sussurro

Ditado por voz local para Windows, com transcrição pelo Whisper e revisão opcional pelo Ollama.

<p align="center">
  <img src="sussurro/assets/sussurro.png" alt="Ícone do Sussurro" width="160">
</p>

<p align="center">
  <a href="https://github.com/Daniellpego/Sussurro/actions/workflows/ci.yml"><img src="https://github.com/Daniellpego/Sussurro/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/Daniellpego/Sussurro/releases/latest"><img src="https://img.shields.io/github/v/release/Daniellpego/Sussurro?label=release" alt="Latest release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Daniellpego/Sussurro" alt="MIT license"></a>
</p>

## Por que o Sussurro

O Sussurro transforma fala em texto no aplicativo que estiver em foco. O áudio, as transcrições e o histórico ficam no computador, sem depender de um serviço de transcrição na nuvem. Quem quiser revisar ou formatar o texto pode usar um modelo local pelo Ollama.

## Instalação

Baixe o instalador adequado na página da [versão mais recente](https://github.com/Daniellpego/Sussurro/releases/latest):

- `SussurroSetup-CPU.exe` funciona sem uma GPU dedicada.
- `SussurroSetup-CUDA.exe` usa uma GPU NVIDIA compatível para acelerar a transcrição.

Os arquivos publicados incluem `checksums-sha256.txt`. Para conferir um instalador no PowerShell:

```powershell
Get-FileHash .\SussurroSetup-CPU.exe -Algorithm SHA256
```

Compare o resultado com a linha correspondente no arquivo de checksums da mesma versão.

## Uso

1. Inicie o Sussurro.
2. Mantenha `Ctrl+Win` pressionado enquanto fala.
3. Solte as teclas para transcrever e colar o texto na janela ativa.

O menu na bandeja do sistema permite trocar o modo de escrita, abrir o histórico, pausar a captura e acessar as configurações.

## Recursos

- Transcrição local com `faster-whisper`.
- Execução em CPU ou GPU NVIDIA com fallback automático para CPU.
- Comandos falados de pontuação e quebra de parágrafo em português.
- Dicionário pessoal e formatação de CPF, CNPJ e número de processo.
- Modos de revisão local pelo Ollama, incluindo texto limpo, formal, resumo e tradução.
- Modos personalizados com instruções editáveis.
- Histórico local com busca e limite de 500 entradas.
- Atalho global de teclado e suporte a botão lateral do mouse.
- Colagem na janela ativa com restauração da área de transferência.

## Requisitos

- Windows 10, build 19041 ou posterior, ou Windows 11.
- 8 GB de RAM para a variante CPU. Para modelos maiores e uso do Ollama, 16 GB são recomendados.
- Microfone integrado ou USB.
- GPU NVIDIA compatível com CUDA somente para a variante CUDA.

Os modelos são baixados no primeiro uso, portanto é necessário acesso à internet durante a configuração inicial. Depois disso, a transcrição e a revisão local funcionam sem enviar o conteúdo ditado para servidores do projeto.

## Desenvolvimento

O projeto usa Python 3.11 ou posterior. No Windows PowerShell:

```powershell
git clone https://github.com/Daniellpego/Sussurro.git
cd Sussurro
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m sussurro
```

Para instalar também as dependências da variante NVIDIA:

```powershell
pip install -r requirements-gpu.txt
```

Antes de enviar uma alteração:

```powershell
ruff check sussurro scripts tests
python scripts/validate_all.py
pytest
```

## Arquitetura

A aplicação separa captura de áudio, transcrição, pós-processamento, revisão por modelo local, armazenamento e interface. O fluxo e as responsabilidades de cada módulo estão descritos em [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Contribuição

Relatos de erro e pull requests são bem-vindos. Leia [CONTRIBUTING.md](CONTRIBUTING.md) antes de começar. Vulnerabilidades devem ser enviadas de forma privada conforme a [política de segurança](SECURITY.md).

## Licença

O Sussurro é distribuído sob a [licença MIT](LICENSE). As licenças das dependências incluídas nos instaladores estão em [docs/THIRD_PARTY_LICENSES.md](docs/THIRD_PARTY_LICENSES.md).
