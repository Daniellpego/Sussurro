@echo off
REM Sussurro — roda a versao de desenvolvimento (codigo do repositorio),
REM sem janela de console. Duplo clique ou: scripts\run-dev.bat
REM Por padrao inicia ativo. Em Ajustes, desative "Ja abrir ativo" para iniciar em espera.
cd /d "%~dp0.."
if not exist ".venv\Scripts\pythonw.exe" (
  echo [Sussurro] venv nao encontrado. Rode: py -3.11 -m venv .venv
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" -m sussurro
