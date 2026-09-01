# Roteiro de Retomada e Próximos Passos — SUSURRO

Documento gerado no encerramento da sessão de 31/08/2026 - 01/09/2026.

---

## 📌 Estado Atual do Projeto
1. **Código e Segurança:**
   - 35/35 testes passando no CI.
   - 0 vulnerabilidades de dependências (CVEs corrigidas em manifestos).
   - Hardening do download do Ollama e validações atômicas de escrita.
2. **Publicações:**
   - Releases oficiais `v0.1.0` e `v0.1.1` publicadas no GitHub com instaladores One-Click CPU (~94 MB) e CUDA (~1.05 GB).
   - Repositório remoto limpo com exatamente 2 branches: `main` e `backup/pre-force-push-7d4e8f1`.

---

## 🎯 Prioridades para a Próxima Sessão

### 1. [ALTA PRIORIDADE] Revalidação Real de Performance (Whisper Large-v3-Turbo + Ollama)
- **Motivo da Pendência:** A auditoria preliminar de performance executada no encerramento usou o modelo `small` (presente em cache local) em CPU pura e sem o daemon do Ollama ativo.
- **Ações:**
  1. Baixar os pesos completos do `faster-whisper-large-v3-turbo` (CTranslate2 INT8).
  2. Iniciar o daemon local do Ollama com o modelo `qwen2.5:7b`.
  3. Medir a latência real de ponta a ponta (fala 5s e 30s) tanto em CPU quanto em GPU NVIDIA (CUDA).
  4. Comparar a taxa de precisão/alucinação e o tempo de resposta entre os presets `raw`, `clean` e especializados (`laudo_birads`, `peticao_inicial`).

### 2. [UX / Melhorias Identificadas]
- Implementar gravador dinâmico de combinação de teclas na tela de Ajustes (`settings_ui.py`) para permitir customizar o atalho de push-to-talk além do padrão `Ctrl+Win`.
- Ajustar contraste da cor `text_tertiary` no dark mode para 4.5:1 (conformidade estrita WCAG 2.1 AA).
