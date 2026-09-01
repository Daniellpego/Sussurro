# Inventário do Repositório

Inventário do estado profissionalizado e completo do **SUSURRO** (v0.1.0).
Arquivos gerados pelo compilador, caches (`.pytest_cache`, `.ruff_cache`, `__pycache__`), diretórios de build (`build/`, `dist/`, `installer/out/`), ambientes virtuais (`.venv/`), modelos de machine learning e arquivos de áudio temporários são deliberadamente excluídos do controle de versão pelo `.gitignore`.

Total de arquivos rastreados no Git: **113 arquivos**.

---

## Árvore de Arquivos Rastreáveis

```text
.github/ISSUE_TEMPLATE/bug_report.yml
.github/workflows/ci.yml
.github/workflows/release.yml
.gitignore
CONTRIBUTING.md
LICENSE
README.md
SECURITY.md
Sussurro (dev).bat
docs/ARCHITECTURE.md
docs/AUDIT.md
docs/INSTALLER_ARCHITECTURE.md
docs/INVENTORY.md
docs/THIRD_PARTY_LICENSES.md
docs/design/README.md
docs/design/design-system.md
docs/design/screens/01-brand-mark.svg
docs/design/screens/02-home.html
docs/design/screens/03-onboarding.html
docs/design/screens/04-historico.html
docs/design/screens/05-ajustes.html
docs/design/screens/06-modos.html
docs/design/screens/07-sobre.html
docs/design/screens/08-overlay-states.html
docs/design/screens/09-system-tray.html
docs/design/stitch-prompt.md
docs/legacy/INITIAL_PLAN.md
installer/README.md
installer/sussurro.iss
pyproject.toml
requirements-dev.txt
requirements-gpu.txt
requirements.txt
scripts/check_imports.py
scripts/screenshot_onboarding.py
scripts/screenshot_pages.py
scripts/smoke.py
scripts/validate_all.py
scripts/verify_gpu.py
sussurro.spec
sussurro/__init__.py
sussurro/__main__.py
sussurro/app.py
sussurro/asr/__init__.py
sussurro/asr/postprocess.py
sussurro/asr/whisper.py
sussurro/assets/chevron_down.png
sussurro/assets/sussurro.ico
sussurro/assets/sussurro.png
sussurro/audio/__init__.py
sussurro/audio/capture.py
sussurro/commands.py
sussurro/cuda_setup.py
sussurro/foreground.py
sussurro/hotkey/__init__.py
sussurro/hotkey/listener.py
sussurro/hotkey/mouse_listener.py
sussurro/inject/__init__.py
sussurro/inject/paste.py
sussurro/llm/__init__.py
sussurro/llm/modes.py
sussurro/llm/ollama.py
sussurro/llm/worker.py
sussurro/setup_check.py
sussurro/sound.py
sussurro/storage/__init__.py
sussurro/storage/autostart.py
sussurro/storage/config.py
sussurro/storage/dictionary.py
sussurro/storage/history.py
sussurro/storage/paths.py
sussurro/ui/__init__.py
sussurro/ui/components/__init__.py
sussurro/ui/components/brand_mark.py
sussurro/ui/components/buttons.py
sussurro/ui/components/chevron.py
sussurro/ui/components/confirm.py
sussurro/ui/components/fields.py
sussurro/ui/components/group.py
sussurro/ui/components/icon_tile.py
sussurro/ui/components/keycap.py
sussurro/ui/components/mode_chip.py
sussurro/ui/components/nav_icons.py
sussurro/ui/components/progress.py
sussurro/ui/components/segmented.py
sussurro/ui/components/title_bar.py
sussurro/ui/components/toggle.py
sussurro/ui/components/window_frame.py
sussurro/ui/fonts.py
sussurro/ui/history_ui.py
sussurro/ui/icons.py
sussurro/ui/modes_ui.py
sussurro/ui/onboarding.py
sussurro/ui/overlay.py
sussurro/ui/settings_ui.py
sussurro/ui/setup_ui.py
sussurro/ui/theme.py
sussurro/ui/tray.py
sussurro/ui/tray_popup.py
sussurro/ui/win_backdrop.py
sussurro/ui/window.py
tests/test_asr_quality.py
tests/test_asr_turbo.py
tests/test_audio.py
tests/test_dictionary_macros.py
tests/test_hardware_fallback.py
tests/test_llm_modes_presets.py
tests/test_llm_pipeline.py
tests/test_ollama.py
tests/test_postprocess_semantic.py
tests/test_robustness.py
tests/test_setup_check.py
tests/test_setup_downloader.py
tests/test_storage.py
```

---

## Distribuição por Camada de Responsabilidade

- **Aplicação Principal (`sussurro/`):** 52 arquivos (motor ASR, áudio, UI PySide6, armazenamento, LLM, injeção de texto e assets).
- **Testes Automatizados (`tests/`):** 13 arquivos (suíte com 35 testes unitários e de integração cobrindo áudio, ASR Turbo, fallback, macros, LLM e armazenamento).
- **Scripts de Validação e Diagnóstico (`scripts/`):** 6 arquivos (validação CI, smoke test, detecção GPU, checagem de imports e renderizadores de tela).
- **Documentação Técnica e Especificações (`docs/`):** 17 arquivos (arquitetura do sistema, arquitetura do instalador, auditoria de segurança, inventário, licenças de terceiros, especificações de design system e telas HTML).
- **Instalação e Empacotamento (`installer/` & `sussurro.spec`):** 3 arquivos (script Inno Setup 6 parametrizado para CPU/CUDA, especificação PyInstaller e documentação de build).
- **Automação e CI/CD (`.github/`):** 3 arquivos (workflows de validação de qualidade `ci.yml`, pipeline de release multi-variante `release.yml` e template de issue).
- **Metadados e Governança na Raiz:** 19 arquivos (`pyproject.toml`, perfis de dependências `requirements*.txt`, `LICENSE` MIT, `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, `.gitignore`, script `.bat` de inicialização rápida).
