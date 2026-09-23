# Changelog

Este arquivo registra as mudanças relevantes de cada versão. O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto usa [versionamento semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Adicionado

- Transcrição parcial no HUD durante gravações mais longas.
- Métricas locais de latência por etapa em `latency.jsonl`.
- Benchmark reproduzível para o modelo `large-v3-turbo` em CPU e CUDA.

### Alterado

- O microfone permanece preparado com um pré-buffer de 300 ms enquanto o app está ativo.
- O modelo de transcrição é carregado e aquecido antes de o atalho ser habilitado.
- Adicionada uma versão em inglês do README em `README.en.md`, com aviso sobre o SmartScreen nas duas versões.
- As notas de cada release são extraídas deste CHANGELOG, e o workflow de release falha se a tag não corresponder à versão do pacote.

### Corrigido

- Comandos de pontuação falados não alteram mais frases comuns, como "ganhei dois pontos no jogo", "a vírgula está errada" ou "chegamos ao ponto final".
- Frases iniciadas depois de "ponto final" ou "nova linha" recebem maiúscula.
- A quebra de linha não se perde quando vem logo depois de um comando de pontuação.
- Alterar qualquer ajuste não descarrega mais o modelo de transcrição; ele só é recarregado quando o modelo escolhido muda, e a escolha do modelo passa a valer sem reiniciar.
- Imagens e arquivos copiados continuam na área de transferência depois do ditado.
- Salvar um ajuste não apaga mais a opção de iniciar com o Windows criada pelo instalador, e a desinstalação remove essa entrada.
- Microfones que aparecem em mais de uma API de áudio do Windows podem ser escolhidos sem erro de "microfone indisponível".
- Textos dos Ajustes corrigidos: padrão da opção de abrir pronto para ditar, aviso de atualização e nome do modelo.

## [0.1.1] - 2026-09-01

### Corrigido

- Limitado o descarregamento no Ollama aos modelos gerenciados pelo Sussurro.
- Recuperado o estado da captura quando o stream de áudio não inicia.
- Preservados histórico, modos e configurações durante a desinstalação.
- Tornado o carregamento do histórico tolerante a entradas inválidas.
- Adicionada escrita atômica para modos e arquivos de configuração.
- Corrigida a digitação de caracteres representados por pares substitutos UTF-16.
- Adicionada verificação TLS, tamanho mínimo e limpeza do instalador temporário do Ollama.
- Atualizadas as versões mínimas de dependências com correções de segurança.

### Adicionado

- Checksums SHA-256 para os instaladores publicados.

## [0.1.0] - 2026-08-31

### Adicionado

- Primeira versão pública para Windows.
- Instaladores separados para CPU e CUDA.
- Transcrição local com Whisper Large v3 Turbo.
- Comandos de pontuação, dicionário pessoal e macros em português.
- Modos de revisão local pelo Ollama.
- Histórico pesquisável e configurações pela bandeja do sistema.

[Não lançado]: https://github.com/Daniellpego/Sussurro/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/Daniellpego/Sussurro/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Daniellpego/Sussurro/releases/tag/v0.1.0
