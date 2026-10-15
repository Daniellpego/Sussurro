# Pesquisa e origem dos visuais do README

Revisão: 15/10/2026. Objetivo: apresentar o Sussurro com identidade própria, tornar o download evidente e explicar o processamento local antes dos detalhes de desenvolvimento. A redação é original. Não foram reproduzidos depoimentos, layouts, capturas ou resultados de outros produtos.

## Fontes consultadas

| Fonte | O que informou a apresentação | Limite |
| :--- | :--- | :--- |
| [faster-whisper, repositório oficial](https://github.com/SYSTRAN/faster-whisper) | Motor de reconhecimento, execução CPU/GPU e dependência do hardware. | Os benchmarks desse projeto não medem o Sussurro; nenhum multiplicador de velocidade foi transferido ao README. |
| [Ollama, repositório oficial](https://github.com/ollama/ollama) | Referência para o motor de revisão local e a preparação de modelos. | O fluxo do Sussurro foi conferido no próprio cliente local; não se infere privacidade de qualquer serviço por usar o nome Ollama. |
| [Ollama: modelos cloud, documentação oficial](https://ollama.com/blog/cloud-models) | A API local também pode encaminhar modelos cloud para execução remota. | As promessas de revisão offline são condicionadas a modelos locais. Loopback não comprova localidade da inferência. |
| [Handy, repositório oficial](https://github.com/cjpais/Handy) | Referência editorial para explicar ditado local e separar download de desenvolvimento. | Não há comparação de desempenho ou promessa de paridade de recursos. |
| [OpenWhispr, repositório oficial](https://github.com/OpenWhispr/openwhispr) | Referência de organização: proposta, download, funcionamento e contribuição. | Esse projeto tem recursos locais e serviços adicionais; suas características não descrevem o Sussurro. |
| [Relato de desenvolvimento de ditado local, r/SideProject](https://www.reddit.com/r/SideProject/comments/1tlagov/i_got_tired_of_typing_being_a_bottleneck_so_i/) | Relato qualitativo de um autor sobre atalho, digitação e processamento no dispositivo. | Não é pesquisa representativa, avaliação do Sussurro nem prova de demanda. Sem citação literal ou endosso. |
| [Discussão sobre Whisper local, r/windowsapps](https://www.reddit.com/r/windowsapps/comments/1v2evx3/i_built_a_free_windows_app_for_running_whisper/) | Identificação de temas a esclarecer: conta, download inicial e funcionamento offline. | O resultado de busca foi usado como contexto exploratório; não comprova funcionalidades ou segurança. |

As buscas também procuraram tutoriais em vídeo. Não houve conteúdo audiovisual verificado suficiente para incorporá-lo como evidência; não se afirma que vídeos foram assistidos. As conclusões sobre este produto vêm do código, dos assets e das releases do próprio Sussurro.

## Promessas conferidas no projeto

| Informação no README | Evidência local |
| :--- | :--- |
| Reconhecimento local com Whisper | [`sussurro/asr/`](../../sussurro/asr), configuração `model_size` em [`config.py`](../../sussurro/storage/config.py). |
| Revisão opcional no computador, com modelos locais | [`ollama.py`](../../sussurro/llm/ollama.py), `OLLAMA_BASE = http://127.0.0.1:11434`; modos em [`modes.py`](../../sussurro/llm/modes.py). O editor aceita tags de modelos; cloud pode enviar texto para fora mesmo usando API local. |
| Raw aplica regras mesmo sem LLM | Modos e pipeline em [`app.py`](../../sussurro/app.py); comandos em [`commands.py`](../../sussurro/commands.py). |
| Histórico de até 500 transcrições | `MAX_ENTRIES` em [`history.py`](../../sussurro/storage/history.py). |
| Dados locais e preservação ao desinstalar | [`paths.py`](../../sussurro/storage/paths.py) e [`sussurro.iss`](../../installer/sussurro.iss). |
| Microfone preparado com pré-buffer | `PREBUFFER_MS = 300` em [`capture.py`](../../sussurro/audio/capture.py). |
| Consulta de atualizações faz acesso à internet | [`updates.py`](../../sussurro/updates.py) e `check_updates` em [`config.py`](../../sussurro/storage/config.py). Não confundir com envio de ditados. |
| Última release disponível e conteúdo dos instaladores | [Release v0.1.2](https://github.com/Daniellpego/Sussurro/releases/tag/v0.1.2), assets CPU/CUDA/checksums; [`CHANGELOG.md`](../../CHANGELOG.md) distingue a preparação da 0.1.3. |

Os requisitos de memória do README são recomendações de partida já documentadas pelo projeto, não uma certificação em todos os dispositivos. Nenhuma captura ou exemplo demonstra uma taxa de acerto, latência ou uso de memória garantidos.

## Assets

| Arquivo | Origem e uso |
| :--- | :--- |
| [`sussurro-hero.png`](../assets/sussurro-hero.png) | Capa original produzida com a ferramenta integrada de geração de imagens; referência visual: ícone existente do Sussurro. Arte conceitual, não captura do aplicativo. |
| [`fluxo-local.svg`](../assets/fluxo-local.svg) e [`local-flow.svg`](../assets/local-flow.svg) | Esquemas vetoriais autorais em português e inglês. Descrevem o fluxo, sem simular uma medição. |
| [`docs/images/`](../images) | Capturas de janelas reais já versionadas no projeto, produzidas por [`screenshot_pages.py`](../../scripts/screenshot_pages.py) com dados fictícios isolados. Não são fotos da área de trabalho do usuário. |

A capa preserva a identidade violeta/rosa do ícone; não substitui o logo da aplicação. O README em inglês usa a mesma arte da marca e traduz a frase em texto acessível.

## Prompt final da capa

Ferramenta: `image_gen`, integrada; sem CLI/API externa. Imagem de referência: `sussurro/assets/sussurro.png`. O arquivo final está salvo no repositório em `docs/assets/sussurro-hero.png`.

```text
Use case: ads-marketing.
Asset type: premium wide GitHub README cover for Sussurro, a local voice dictation application for Windows.
Primary request: an exceptionally beautiful original editorial brand cover conveying voice becoming written words, quietly on your own computer.
Reference image: existing Sussurro icon, use its five rounded vertical waveform bars and violet-to-magenta gradient as brand inspiration, preserve that visual identity, do not redesign the logo.
Composition: wide panoramic 2.5:1 landscape, strong ample margins and readable thumbnail, left side has elegant large clean white typographic wordmark SUSSURRO. Beneath it smaller exact Portuguese text: "Sua voz. Seu texto. Seu computador." Right side has a sculptural acoustic waveform made of softly illuminated translucent violet and rose glass ribbons, flowing into fine luminous horizontal lines resembling text. Rich near-black obsidian backdrop, subtle film grain and delicate atmospheric depth, precision studio lighting, sophisticated restrained contrast, ultra refined product editorial design. The voice sculpture feels tactile and art-directed, not a generic cyberpunk graphic. Sparse use of luminous magenta, lavender and electric purple, generous negative space.
Text (verbatim): "SUSSURRO"; "Sua voz. Seu texto. Seu computador."
Constraints: no application screenshot, no fake UI, no performance metrics, no laptop or microphone hardware, no additional text, no cloud symbols, no watermarks. This is conceptual brand art, not a product screenshot. Final image must feel coherent with the supplied icon.
```
