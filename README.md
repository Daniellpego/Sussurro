# Sussurro

Alternativa **local, gratuita e offline** ao Wispr Flow / SuperWhisper.

Push-to-talk (`Ctrl+Win` ou botão do mouse), transcrição em PT-BR + termos em inglês via **faster-whisper**, pós-processamento opcional com **LLM local** (Ollama + Qwen) em modos editáveis, e colagem no app em foco.

Arquitetura e decisões: [`PLAN.md`](./PLAN.md).

## O que você precisa

| Requisito | Nota |
|-----------|------|
| **Windows 10/11** | Alvo oficial |
| **GPU NVIDIA + CUDA** | Ideal (RTX 4070 Ti 12 GB ou similar). Sem GPU, o app tenta **CPU** (bem mais lento) |
| **Microfone** | Qualquer um do sistema |
| **Ollama** (opcional) | Só pros modos com IA (Clean, Email…). Raw funciona só com Whisper |

## Setup (dev)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
python -m sussurro
```

Smoke do ASR:

```powershell
python scripts\smoke.py
python scripts\test_asr_quality.py
```

## Uso diário (local)

### Abrir (dev — código mais novo)

Duplo clique em **`Sussurro (dev).bat`**  
(ou `.\.venv\Scripts\python.exe -m sussurro`)

### Fluxo

1. O app sobe **em espera** (quase sem VRAM)  
2. Bandeja → **Ativar Sussurro**  
3. Segure **Ctrl+Win** (ou botão do mouse) e fale  
4. Solte — HUD → texto cola no app em foco  
5. Quando acabar: bandeja → **Desativar · economizar memória**

### Dicas

- **Raw** = só Whisper (sem Ollama)  
- **Clean / Email / …** = precisa do Ollama + Qwen (sobe sob demanda)  
- **Dicionário** em Ajustes (semente + sugestões)  
- Colar **Automático**: Ctrl+V → Shift+Insert → digitar  
- App alvo **como Admin** + Sussurro normal = colagem bloqueada (UIPI)  
- Validação rápida: `python scripts\validate_all.py`

### Perfis de ASR (mesmo large-v3; só muda esforço de decode)

- **Qualidade** (padrão) · **Equilíbrio** · **Leve**  

GPU falhou? Cai pra int8 e depois CPU, com aviso.

## Build instalável

Ver [`installer/README.md`](./installer/README.md) (PyInstaller + Inno Setup).

## Status

App usável no dia a dia (hotkey, HUD, modos CRUD, histórico, tray, dicionário, paste robusto, fallback GPU→CPU).  
Não é produto “pra qualquer PC sem GPU” no mesmo nível de latência.
