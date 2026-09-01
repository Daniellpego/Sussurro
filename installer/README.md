# Construindo o Instalador do Sussurro (Inno Setup 6)

O processo de build utiliza o **PyInstaller** para compilar o executável e seus módulos, e o **Inno Setup 6** para gerar o instalador final executável para Windows (`.exe`).

O pipeline suporta duas variantes: **CPU** (leve, compatível com qualquer PC) e **CUDA** (otimizada com bibliotecas da NVIDIA para placas RTX/GTX).

---

## 1. Preparar o Ambiente

Na raiz do repositório:

```powershell
# Criação do ambiente virtual
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Dependências de desenvolvimento e build
pip install -r requirements-dev.txt
```

Para compilar a **Variante CUDA**, certifique-se de instalar também:
```powershell
pip install -r requirements-gpu.txt
```

---

## 2. Compilação com PyInstaller

### A) Compilar Variante CPU
```powershell
$env:SUSSURRO_VARIANT = "cpu"
pyinstaller --noconfirm sussurro.spec
```

### B) Compilar Variante CUDA
```powershell
$env:SUSSURRO_VARIANT = "cuda"
pyinstaller --noconfirm sussurro.spec
```

O bundle da aplicação será gerado em:
```text
dist\Sussurro\
```

---

## 3. Gerar o Instalador com Inno Setup 6

Certifique-se de ter o Inno Setup 6 instalado (ex: `choco install innosetup`).

### A) Gerar Instalador CPU (`SussurroSetup-CPU.exe`)
```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DMyAppVersion="v0.1.0" /DAppVariant="CPU" installer\sussurro.iss
```

### B) Gerar Instalador CUDA (`SussurroSetup-CUDA.exe`)
```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DMyAppVersion="v0.1.0" /DAppVariant="CUDA" installer\sussurro.iss
```

Os instaladores finais serão salvos em:
```text
installer\out\SussurroSetup-CPU.exe     (~110 MB)
installer\out\SussurroSetup-CUDA.exe    (~1.0 GB)
```

---

## 4. Comportamento e Segurança do Instalador

- **Instalação Sem Privilégios Administrativos:** Instala por padrão em `%LOCALAPPDATA%\Programs\Sussurro\` sem requerer elevação de UAC.
- **Atalhos e Inicialização:** Cria atalhos no Menu Iniciar e, opcionalmente, na Área de Trabalho e inicialização com o Windows (`HKCU`).
- **Preservação de Dados:** A rotina de desinstalação preserva expressamente o diretório `%APPDATA%\Sussurro` (histórico de ditados, dicionário e modos customizados) para proteger o usuário contra perda acidental de dados.
