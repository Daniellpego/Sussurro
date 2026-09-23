# Changelog

Este arquivo registra as mudanças relevantes de cada versão. O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto usa [versionamento semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Alterado

- Nova onda de voz no indicador de gravação: nove barras arredondadas e simétricas, no estilo do logo, que sobem e descem com a voz sem rolar para o lado, com um gradiente único e animação a 60 fps. Em silêncio, viram pontos que respiram devagar.

### Corrigido

- O conteúdo do indicador de gravação ficava desalinhado para cima depois do primeiro segundo.

## [0.1.2] - 2026-09-23

### Adicionado

- Transcrição parcial no HUD durante gravações mais longas.
- Métricas locais de latência por etapa em `latency.jsonl`.
- Benchmark reproduzível para o modelo `large-v3-turbo` em CPU e CUDA.
- Fontes Geist e Geist Mono (OFL) e sons de feedback versionados no repositório; o build falha se algum desses arquivos faltar.
- Auditoria de dependências (`pip-audit`) no CI.

### Alterado

- O microfone permanece preparado com um pré-buffer de 300 ms enquanto o app está ativo.
- O modelo de transcrição é carregado e aquecido antes de o atalho ser habilitado.
- Adicionada uma versão em inglês do README em `README.en.md`, com aviso sobre o SmartScreen nas duas versões.
- As notas de cada release são extraídas deste CHANGELOG, e o workflow de release falha se a tag não corresponder à versão do pacote.
- `requires-python` limitado a 3.11 e 3.12, pois o NumPy 1.x não tem pacotes para o Python 3.13.

### Corrigido

- Comandos de pontuação falados não alteram mais frases comuns, como "ganhei dois pontos no jogo", "a vírgula está errada" ou "chegamos ao ponto final".
- Frases iniciadas depois de "ponto final" ou "nova linha" recebem maiúscula.
- A quebra de linha não se perde quando vem logo depois de um comando de pontuação.
- Alterar qualquer ajuste não descarrega mais o modelo de transcrição; ele só é recarregado quando o modelo escolhido muda, e a escolha do modelo passa a valer sem reiniciar.
- Imagens e arquivos copiados continuam na área de transferência depois do ditado.
- Salvar um ajuste não apaga mais a opção de iniciar com o Windows criada pelo instalador, e a desinstalação remove essa entrada.
- Microfones que aparecem em mais de uma API de áudio do Windows podem ser escolhidos sem erro de "microfone indisponível".
- Textos dos Ajustes corrigidos: padrão da opção de abrir pronto para ditar, aviso de atualização e nome do modelo.
- Ditar logo depois de um ditado anterior não esconde mais o indicador de gravação, não cola o texto anterior com Ctrl+Win pressionados e não cancela a nova gravação.
- Mensagens do HUD exibidas com ele fechado, como "microfone indisponível", voltam a sumir sozinhas.
- Resultados de um ditado anterior não sobrescrevem o HUD e o status da gravação atual.
- Teclas enviadas pelo próprio Sussurro ou por outros programas não acionam nem cancelam o atalho, e uma tecla Ctrl ou Win "presa" após Win+L deixa de disparar gravações.
- Falhas da transcrição parcial não aparecem mais como erro durante a gravação.
- O microfone não abre dois fluxos ao mesmo tempo, e um microfone desconectado é reaberto ou informado.
- Em janelas executadas como administrador, o texto fica na área de transferência com o aviso para colar com Ctrl+V, em vez de indicar "Colado" sem colar.
- A configuração inicial permite tentar de novo os downloads do Whisper e do Qwen, iniciar o Ollama instalado e mostra o motivo das falhas.
- A instalação automática do Ollama só é considerada concluída quando o instalador termina.
- Arquivos de configuração, histórico, dicionário, macros e modos ilegíveis são preservados como `*.corrupt-<data>` antes de voltar aos padrões.
- Modelo de IA não baixado aparece como tal no HUD e numa notificação, em vez de "erro na IA".
- A janela principal não abre mais fora da tela depois que um monitor é desconectado.
- Atualizar ou trocar entre as variantes CPU e CUDA remove os arquivos da instalação anterior.
- As abas dos Ajustes rolam: em telas baixas, os cards de Modos se sobrepunham e a seção Desempenho ficava espremida.
- Notas longas dos Ajustes quebram linha em vez de serem cortadas.
- Transcrições longas no Histórico mostram duas linhas com reticências em vez de cobrir o chip do modo.

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

[Não lançado]: https://github.com/Daniellpego/Sussurro/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/Daniellpego/Sussurro/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/Daniellpego/Sussurro/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Daniellpego/Sussurro/releases/tag/v0.1.0
