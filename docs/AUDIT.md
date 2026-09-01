# Auditoria Técnica e de Segurança do Repositório

Data da revisão: 2026-08-31 / 2026-09-01.

---

## 1. Escopo da Auditoria

Auditoria abrangente e independente cobrindo:
1. **Estrutura e Qualidade do Código:** Verificação estática de tipos, linting (Ruff), imports circulares e compilação Python 3.11+.
2. **Segurança do Histórico Git:** Varredura profunda em todo o grafo de commits à procura de tokens, chaves de API, credenciais do Windows ou segredos embutidos.
3. **Vulnerabilidades em Dependências (CVEs):** Análise de pacotes via `pip-audit` contra bancos de dados oficiais de segurança.
4. **Isolamento de Recursos e Integridade do Sistema Operacional:** Validação de comportamento do instalador no `%APPDATA%`, isolamento de processos do Ollama na VRAM, validação TLS e de integridade no download de executáveis.
5. **Cadeia de Confiança de CI/CD:** Verificação de permissões mínimas no GitHub Actions (`contents: read` / `contents: write`), geração nativa de checksums SHA-256 no runner e versionamento de actions.
6. **Conformidade de Licenciamento:** Análise da licença principal (MIT) e atribuição de todas as dependências redistribuídas (PySide6/LGPLv3, CTranslate2/MIT, Ollama/MIT, Qwen 2.5/Apache 2.0, NVIDIA CUDA EULA).

---

## 2. Histórico de Achados e Resoluções

| Severidade | Módulo / Arquivo | Achado Inicial | Status e Resolução |
|---|---|---|---|
| **Crítico** | `sussurro/app.py` | Encerramento do LLM chamava `unload_all()` descarregando modelos do Ollama pertencentes a outros aplicativos do usuário. | **Corrigido:** `unload_models` agora descarrega estritamente os modelos gerenciados pelo Sussurro (`qwen2.5:*`). |
| **Alto** | `sussurro/audio/capture.py` | Falha ao iniciar `InputStream` podia deixar `_stream` preenchido e travar o estado de gravação. | **Corrigido:** Tratamento defensivo com recuperação automática de estado em caso de exceção de áudio. |
| **Alto** | `requirements.txt` / `requirements-dev.txt` | Sub-dependências transitivas e pacotes podiam permitir versões antigas com vulnerabilidades conhecidas (ctranslate2 <4.6.0, onnxruntime <1.23.0, pyinstaller <6.13.0, pytest <9.0.0). | **Corrigido:** Fixadas explicitamente as versões mínimas seguras: `ctranslate2>=4.6.0`, `onnxruntime>=1.23.0`, `pyinstaller>=6.13.0,<7` e `pytest>=9.0.0`. |
| **Alto** | `requirements.txt` | `httpx` e `huggingface_hub` eram imports diretos sem declaração explícita de versões. | **Corrigido:** Dependências devidamente pinadas e segmentadas em base, GPU e dev. |
| **Alto** | `sussurro/setup_check.py` | Executável do Ollama era baixado sem checagem de tamanho mínimo de arquivo e deixava resíduo em `%TEMP%`. | **Corrigido:** Adicionada validação de tamanho mínimo (>10 MB), TLS estrito (`verify=True`) e remoção garantida do executável temporário via `finally`. |
| **Alto** | `installer/sussurro.iss` | Desinstalador apagava indiscriminadamente o diretório `%APPDATA%\Sussurro` contendo transcrições do usuário. | **Corrigido:** Desinstalador preserva `%APPDATA%\Sussurro` (histórico, modos customizados e configurações). |
| **Médio** | `sussurro/storage/history.py` | Uma entrada corrompida podia quebrar o carregamento de todo o histórico. | **Corrigido:** Parser tolerante a falhas por linha e escrita atômica com arquivo temporário. |
| **Médio** | `sussurro/llm/modes.py` | `modes.json` era salvo sem escrita atômica. | **Corrigido:** Escrita atômica via `replace` e validação estrita de IDs. |
| **Médio** | `sussurro/inject/paste.py` | Digitação Win32 truncava caracteres fora do BMP (ex: emojis). | **Corrigido:** Suporte nativo a UTF-16 surrogate pairs com API Win32 `SendInput`. |
| **Médio** | `sussurro.spec` | Compilador exigia caminhos fixos de fontes e falhava na ausência de arquivos opcionais. | **Corrigido:** Inclusão dinâmica e tolerante a assets ausentes com suporte a flags multi-variante (CPU vs CUDA). |
| **Baixo** | Documentação e Testes | Testes misturados com scripts, licença pendente e ausência de release pipeline. | **Corrigido:** 35 testes em `tests/`, `LICENSE` MIT, `THIRD_PARTY_LICENSES.md`, `SECURITY.md`, `CONTRIBUTING.md` e workflow `release.yml`. |

---

## 3. Auditoria de Segredos e Credenciais no Git

- **Metodologia:** Varredura automatizada linha a linha através de `git log -p --all` cobrindo 16.996 linhas de histórico de diffs.
- **Padrões testados:** GitHub Tokens (`ghp_`, `github_pat_`), OpenAI Keys (`sk-`), AWS Access Keys (`AKIA`/`ASIA`), Hugging Face Tokens (`hf_`), Google Cloud Keys (`AIzaSy`), Private Keys PEM/RSA, Bearer Tokens e credenciais em variáveis de ambiente.
- **Resultado:** **0 segredos ou credenciais expostos** em todo o histórico do repositório.

---

## 4. Auditoria de Vulnerabilidades de Dependências (CVEs)

- **Ferramenta utilizada:** `pip-audit 2.10.1` contra o banco de dados oficial do PyPI / OSV.
- **Comando executado:** `pip-audit -r requirements.txt -r requirements-gpu.txt -r requirements-dev.txt` e auditoria global do ambiente (`pip-audit -v`).
- **Versões mínimas seguras fixadas:**
  - `ctranslate2>=4.6.0` (patch de segurança para PYSEC-2026-88)
  - `onnxruntime>=1.23.0` (patch de segurança para GHSA-4hvw-gvg5-4p73, GHSA-5254-2qvc-mrhf, etc.)
  - `pyinstaller>=6.13.0,<7` (patch de segurança para GHSA-24ch-2w7p-2hff)
  - `pytest>=9.0.0` (patch de segurança para PYSEC-2026-1845)
- **Resultado:** **0 vulnerabilidades conhecidas encontradas** nas dependências declaradas e no ambiente Python.

---

## 5. Validação Automatizada da Suíte

- **Linter:** `ruff check sussurro scripts tests installer` -> **0 erros**.
- **Validação de Módulos:** `python scripts/validate_all.py` -> **100% dos módulos compilando e carregando**.
- **Suíte de Testes:** `pytest -v` -> **35/35 testes passando** com cobertura em ASR, pipeline de áudio, macros de pontuação, detecção de GPU, isolamento Ollama e armazenamento atômico.
