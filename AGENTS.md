# 🎙️ Diretrizes de Engenharia e Governança: Sussurro (Antigravity System)

Este documento estabelece as diretrizes arquiteturais, padrões de segurança e critérios de qualidade para o desenvolvimento do **Sussurro**.

---

## 🎯 1. Tese do Produto & Soberania de Dados (Local-First)
> **"Ditado por voz e transcrição 100% locais no Windows, garantindo privacidade absoluta e zero dependência de nuvem."**

1. **Privacidade Inegociável:** Nenhum dado de áudio, transcrição bruta, histórico ou credencial de usuário pode ser transmitido para servidores de terceiros.
2. **Modelo Híbrido GPU/CPU:** O pipeline utiliza `faster-whisper` (`large-v3-turbo`) com tentativa inicial em GPU NVIDIA (CUDA) e fallback transparente e resiliente para CPU (`int8`) caso o driver ou a VRAM falhem.
3. **Pós-processamento Inteligente:** Correção determinística de pontuação em PT-BR e macros de formatação ocorrem antes de qualquer chamada opcional a LLMs locais via Ollama (`127.0.0.1:11434`).

---

## 🛠️ 2. Padrões de Engenharia (Antigravity Senior)

### Definition of Done (Critério Inegociável de Conclusão)
Toda alteração de código ou nova funcionalidade deve obrigatoriamente cumprir:
1. **Zero Erros no Linter:** Executar `ruff check sussurro scripts tests` sem nenhuma supressão indevida.
2. **100% de Aprovação nos Testes:** Executar `pytest tests` e garantir que toda a suíte passe sem falhas.
3. **Validação Geral de Módulos:** Executar `python scripts/validate_all.py` (garantindo sintaxe, integridade de imports e testes rápidos).
4. **Desacoplamento de UI:** Nenhuma operação pesada de áudio, transcrição ou inferência de LLM pode rodar na thread principal da interface (PySide6). Use sempre `QThread` assíncrona.
5. **Persistência Atômica:** Qualquer escrita em disco em `%APPDATA%/Sussurro` deve usar `write_text_atomic` com arquivo temporário para evitar corrupção de dados.

---

## 🧠 3. Integração com o Segundo Cérebro (Obsidian)
- O Sussurro atua como motor oficial de transcrição de áudios, reuniões e mentorias para a pasta `RAW/` do cofre (`e:\Dados\RAW\`).
- O módulo `sussurro.transcribe_file` permite processar gravações em lote diretamente para o fluxo de compilação da base de conhecimento.
