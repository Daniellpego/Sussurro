# Auditoria técnica do repositório

Data da revisão: 2026-08-31.

## Escopo

Revisão de estrutura, sintaxe, imports, dependências, persistência, integração Ollama, captura de áudio, build, instalador, documentação, artefatos versionados e sinais de segredos no conteúdo do projeto.

## Achados antes das correções

| Severidade | Local | Achado |
|---|---|---|
| Crítico | `sussurro/app.py` | Liberação/encerramento do LLM chamava `unload_all()` e podia descarregar modelos do Ollama pertencentes a outros aplicativos. |
| Alto | `sussurro/audio/capture.py` | Falha ao iniciar `InputStream` podia deixar `_stream` preenchido e travar o estado de gravação. |
| Alto | `requirements.txt` | `httpx` e `huggingface_hub` eram imports diretos sem declaração explícita. |
| Alto | `sussurro/setup_check.py` | Qualquer tag `qwen2.5:*` podia ser aceita como se fosse o modelo exato configurado. |
| Alto | `sussurro.spec` | Assets opcionais eram exigidos por caminho fixo, podendo quebrar o build quando ausentes. |
| Médio | `sussurro/storage/history.py` | Uma entrada antiga/malformada podia invalidar o carregamento do histórico. |
| Médio | `sussurro/llm/modes.py` | `modes.json` era salvo sem escrita atômica. |
| Médio | `sussurro/llm/modes.py` | Operações com ID inexistente podiam atingir o modo de fallback. |
| Médio | `sussurro/setup_check.py` | Pull do Qwen podia terminar sem confirmação explícita e ainda seguir como sucesso. |
| Médio | `sussurro/app.py` | Fallback de erro inesperado do LLM podia usar texto anterior ao pós-processamento/comandos. |
| Médio | `sussurro/inject/paste.py` | Digitação Win32 truncava caracteres Unicode fora do BMP, como parte dos emojis. |
| Médio | `installer/sussurro.iss` | URL pública era placeholder e a desinstalação apagava automaticamente os dados do usuário. |
| Baixo | Repositório | Testes estavam misturados com scripts, `.gitignore` duplicava regras e havia imports mortos/documentação divergente. |

## Correções

- Isolamento de modelos Ollama: o Sussurro descarrega apenas os modelos que ele próprio conhece/usa.
- Shutdown idempotente para impedir limpeza duplicada.
- Recorder recupera estado corretamente quando o stream falha.
- Modelo Qwen validado pelo nome/tag exato e pull só conclui com confirmação de sucesso.
- Histórico tolera linhas inválidas individualmente e campos futuros desconhecidos.
- `modes.json` passou a usar escrita atômica e IDs inválidos são rejeitados nas mutações.
- Fallback do LLM preserva o texto já pós-processado.
- Entrada Unicode Win32 usa unidades UTF-16 e suporta pares substitutos.
- PyInstaller trata fontes/sons customizados como opcionais.
- Desinstalador preserva `%APPDATA%\Sussurro`.
- Dependências separadas em base, GPU e desenvolvimento.
- Testes movidos para `tests/` e validador separado de smoke tests de hardware.
- Documentação reorganizada sob `docs/`.
- Exports gerados/redundantes de design (PNGs renderizados e bundle de handoff) foram removidos; os protótipos HTML e especificações fonte foram preservados. Isso não afeta o runtime.

## Validação automatizada

A suíte de CI executa em Windows com Python 3.11:

1. instalação de dependências;
2. Ruff;
3. compilação/importação dos módulos;
4. testes automatizados sem GPU/Ollama/microfone real.

Testes de CUDA, microfone e latência continuam sendo validações de hardware e devem ser executados em uma máquina Windows compatível.

## Segredos

O conteúdo versionável foi varrido por padrões de chaves privadas, tokens e credenciais comuns. Nenhum segredo aparente foi identificado. O histórico do GitHub deve continuar sendo tratado como parte da superfície de auditoria antes de publicar credenciais futuramente.

## Decisão pendente

A licença do projeto não foi escolhida pelo proprietário. Nenhum `LICENSE` foi criado nesta revisão.
