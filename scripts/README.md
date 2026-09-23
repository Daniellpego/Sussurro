# Scripts

Utilitários de desenvolvimento, diagnóstico e release. Rode a partir da raiz do repositório, com o ambiente virtual ativo.

| Script | Para que serve |
|---|---|
| `run-dev.bat` | Abre o Sussurro a partir do código do repositório, sem janela de console. |
| `validate_all.py` | Validação rápida antes de um commit: sintaxe, imports e testes, sem GPU, microfone ou Ollama. |
| `check_imports.py` | Importa todos os módulos do pacote para detectar erros de import. |
| `benchmark_latency.py` | Mede a latência de transcrição com um arquivo WAV (`--device cpu` ou `cuda`). |
| `verify_gpu.py` | Confere se o Whisper carrega na GPU (CUDA, cuDNN e CTranslate2). |
| `smoke.py` | Grava alguns segundos do microfone e transcreve na GPU, para testar a pilha completa. |
| `screenshot_pages.py` | Gera as capturas das janelas usadas no README (`--out docs/images`). |
| `screenshot_onboarding.py` | Captura as etapas do assistente de primeira execução. |
| `generate_sounds.py` | Recria os sons de feedback em `sussurro/assets/sounds`. |
| `release_notes.py` | Extrai as notas de uma versão do CHANGELOG; usado pelo workflow de release. |
