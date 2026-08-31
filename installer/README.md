# Construindo o SussurroSetup.exe

O processo usa PyInstaller para gerar o aplicativo e Inno Setup 6 para gerar o instalador.

## 1. Preparar o ambiente

Na raiz do projeto:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Se o build deve incluir o runtime CUDA via wheels Python:

```powershell
pip install -r requirements-gpu.txt
```

## 2. Empacotar com PyInstaller

```powershell
pyinstaller --noconfirm sussurro.spec
```

Saída:

```text
dist\Sussurro\
```

Valide o executável antes de gerar o instalador:

```powershell
.\dist\Sussurro\Sussurro.exe
```

O tamanho final depende das bibliotecas CUDA presentes no ambiente de build.

## 3. Gerar o instalador

Instale Inno Setup 6 e execute:

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\sussurro.iss
```

Saída:

```text
installer\out\SussurroSetup.exe
```

## Comportamento do instalador

- Instala em `%LOCALAPPDATA%\Programs\Sussurro\` sem exigir instalação em `Program Files`.
- Cria atalho no Menu Iniciar.
- Permite atalho opcional na área de trabalho.
- Permite iniciar com o Windows via HKCU.
- **Preserva** `%APPDATA%\Sussurro` durante a desinstalação para evitar perda silenciosa de configuração, modos e histórico.
- O primeiro uso pode baixar o modelo Whisper caso ainda não esteja no cache local.

Para reset completo, os dados em `%APPDATA%\Sussurro` devem ser removidos manualmente pelo usuário.

## Build limpo

```powershell
Remove-Item -Recurse -Force build, dist, installer\out -ErrorAction SilentlyContinue
pyinstaller --noconfirm sussurro.spec
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\sussurro.iss
```
