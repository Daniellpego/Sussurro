# Política de Segurança (Security Policy)

O projeto **SUSURRO** leva a segurança e a privacidade dos seus usuários com máxima seriedade. Esta política descreve como reportar potenciais vulnerabilidades de forma responsável e como garantimos a proteção de dados locais.

---

## 1. Princípios de Segurança e Privacidade

- **Local-First & Zero Telemetria Oculta:** O processamento de áudio (ASR) e inferência de linguagem (LLM) são executados 100% no dispositivo local do usuário (`127.0.0.1`). Nenhuma gravação, transcrição, histórico ou áudio é enviado para servidores de terceiros ou serviços de nuvem do projeto.
- **Isolamento de Dados do Usuário:** Os dados de configuração, histórico e dicionário residem no diretório `%APPDATA%\Sussurro` e são preservados durante desinstalações/atualizações para evitar perda acidental de dados.
- **Isolamento de Recursos (Ollama):** As rotinas de gerenciamento de VRAM do Sussurro descarregam exclusivamente os modelos LLM que ele próprio gerencia, sem afetar instâncias ou modelos externos do usuário.
- **Cadeia de Confiança de Releases:** Todos os instaladores executáveis publicados no GitHub Releases acompanham manifesto oficial de checksums SHA-256 gerado dentro do pipeline automatizado do GitHub Actions.

---

## 2. Como Reportar uma Vulnerabilidade (Divulgação Responsável)

Se você identificou uma vulnerabilidade de segurança (como execução de código não autorizada, contorno de isolamento, injeção de comandos, vazamento de memória ou falha na cadeia de integridade do instalador), **NÃO abra uma issue pública**.

Em vez disso, utilize um dos seguintes canais:

1. **GitHub Security Advisory Privado (Recomendado):**
   - Acesse a aba **Security** do repositório: [Report a vulnerability](https://github.com/Daniellpego/Sussurro/security/advisories/new).
   - Esse canal permite comunicação criptografada e coordenada antes da divulgação pública.

2. **Contato Direto com os Mantenedores:**
   - Envie um relatório detalhado para o time de desenvolvimento através do GitHub Security Advisories.

---

## 3. Informações a Incluir no Relatório

Para acelerar a triagem e correção, inclua:
- Versão do Sussurro e commit afetado (ex: `v0.1.0` / commit SHA).
- Versão do Windows e arquitetura (ex: Windows 11 23H2 x64).
- Passos detalhados e reproduzíveis para disparar o problema (Proof of Concept).
- Impacto esperado e potencial cenário de risco.

> **Importante:** Nunca anexe arquivos reais do seu `%APPDATA%\Sussurro` contendo transcrições confidenciais, chaves privadas ou dados pessoais em relatórios de vulnerabilidade. Utilize dados sintéticos / fictícios para demonstrar o PoC.

---

## 4. Prazos e Compromisso de Resposta

- **Confirmação inicial:** Responderemos em até **48 horas** acusando o recebimento do relatório.
- **Triagem e Avaliação:** Avaliaremos a gravidade e o escopo da correção em até **5 dias úteis**.
- **Publicação do Patch:** Uma versão corretiva será disponibilizada com prioridade máxima acompanhada das devidas atribuições aos pesquisadores de segurança que colaborarem responsavelmente.
