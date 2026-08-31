# Contribuindo com o Sussurro

## Ambiente

O alvo oficial é Windows 10/11 e Python 3.11+.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Para validar CUDA localmente, instale também as dependências de `requirements-gpu.txt`.

## Antes do pull request

```powershell
ruff check sussurro scripts tests
python scripts\validate_all.py
```

Mudanças relacionadas a áudio, GPU, hotkeys globais ou colagem Win32 também devem ser verificadas manualmente no Windows real.

## Organização

- Código da aplicação: `sussurro/`.
- Testes automatizados: `tests/`.
- Scripts operacionais/smoke: `scripts/`.
- Documentação: `docs/`.
- Assets necessários em runtime: `sussurro/assets/`.

Não versione `.venv`, caches, modelos baixados, builds, dumps de `%APPDATA%`, logs, credenciais ou arquivos de áudio pessoais.

## Escopo das mudanças

Prefira PRs pequenos e com comportamento explícito. Correções devem incluir teste de regressão quando for viável. Evite alterar o fluxo de push-to-talk, foco da janela ou persistência sem explicar o impacto no PR.
