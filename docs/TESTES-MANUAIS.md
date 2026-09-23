# Testes manuais no Windows

Os testes automáticos não cobrem microfone, atalhos globais, colagem em outros aplicativos nem o instalador. Antes de publicar uma versão, confira esta lista num Windows real. Leva cerca de 15 minutos.

## Preparar

```powershell
git pull
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
scripts\run-dev.bat
```

Se ainda não houver ambiente virtual, siga a seção Desenvolvimento do [README](../README.md).

## Ditado

- [ ] Segure <kbd>Ctrl</kbd> + <kbd>Win</kbd>, fale uma frase e solte. O texto aparece no Bloco de Notas.
- [ ] Durante a gravação, a onda do indicador sobe e desce com a voz e fica centralizada na pílula.
- [ ] Dite “olá vírgula tudo bem ponto final nova linha obrigado”. Resultado: “Olá, tudo bem.” e “Obrigado” na linha de baixo.
- [ ] Dite “ganhei dois pontos no jogo”. O texto sai igual, sem dois-pontos.
- [ ] Logo depois de “Colado”, segure o atalho de novo e dite outra frase. Os dois textos aparecem, na ordem.
- [ ] Aperte <kbd>Win</kbd> + <kbd>L</kbd>, desbloqueie e aperte só <kbd>Ctrl</kbd>. Nenhuma gravação começa.

## Colagem

- [ ] Copie uma imagem, dite algo e depois cole a imagem num editor. A imagem continua na área de transferência.
- [ ] Abra o Prompt de Comando como administrador e dite nele. Aparece o aviso para colar com <kbd>Ctrl</kbd> + <kbd>V</kbd>, e colar funciona.

## Janelas e menus

- [ ] O menu da bandeja abre com ícones, e “Pausar e liberar memória” e “Retomar ditado” funcionam.
- [ ] Nos Ajustes, todas as abas rolam e nada fica sobreposto.
- [ ] Troque o microfone e o idioma em Ajustes > Entrada e Ajustes > Modelos. A janela principal mostra os novos valores.
- [ ] Escolha um microfone USB e dite.
- [ ] Mude um ajuste qualquer e dite logo em seguida. Não há espera para recarregar o modelo.

## Instalador (depois da release)

- [ ] Instale por cima da versão anterior. O app abre e mantém histórico e configurações.
- [ ] Marque “Iniciar com o Windows” no instalador, abra os Ajustes e confira que a opção aparece ligada.
- [ ] Desinstale. A entrada de início automático some do Gerenciador de Tarefas > Aplicativos de inicialização.

Se algo falhar, abra uma issue com os passos e o trecho relevante de `%APPDATA%\Sussurro\sussurro.log`, sem transcrições ou dados pessoais.
