# Inventário do repositório

Inventário do estado profissionalizado do Sussurro. Arquivos gerados, caches, ambientes virtuais e modelos baixados são deliberadamente excluídos.

Total listado: **105 arquivos**.

```text
.github/ISSUE_TEMPLATE/bug_report.yml
.github/workflows/ci.yml
.gitignore
CONTRIBUTING.md
LICENSE
README.md
SECURITY.md
Sussurro (dev).bat
docs/ARCHITECTURE.md
docs/AUDIT.md
docs/INVENTORY.md
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
tests/test_audio.py
tests/test_llm_pipeline.py
tests/test_ollama.py
tests/test_robustness.py
tests/test_setup_check.py
tests/test_storage.py
```

## Responsabilidade por área

- `sussurro/`: código executável da aplicação.
- `tests/`: testes automatizados e regressões.
- `scripts/`: diagnóstico, smoke tests e utilitários de captura visual.
- `docs/`: arquitetura, auditoria, inventário, plano histórico e referências de design.
- `installer/`: empacotamento final com Inno Setup.
- `.github/`: CI e templates de colaboração.
- arquivos `requirements*.txt`: perfis de dependência base, GPU e desenvolvimento.
- `LICENSE`: licença MIT do projeto.
