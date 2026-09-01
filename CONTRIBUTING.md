# Contribuindo

Obrigado pelo interesse em melhorar o Sussurro. Antes de escrever código, procure por uma issue existente. Para mudanças maiores, abra uma issue curta descrevendo o problema e a solução proposta.

## Preparar o ambiente

O desenvolvimento e os testes de integração devem ser feitos no Windows 10 ou 11 com Python 3.11 ou posterior.

```powershell
git clone https://github.com/Daniellpego/Sussurro.git
cd Sussurro
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

Para trabalhar na variante NVIDIA, instale também `requirements-gpu.txt`.

## Relatar um erro

Abra um bug report e informe:

- versão do Sussurro;
- variante CPU ou CUDA;
- versão e edição do Windows;
- passos mínimos para reproduzir;
- resultado esperado e resultado observado;
- trecho relevante do log, sem transcrições ou dados pessoais.

## Enviar um pull request

Mantenha cada pull request focado em um problema. Correções devem incluir um teste de regressão quando isso for viável. Descreva qualquer verificação manual necessária para áudio, atalhos globais, GPU ou colagem no Windows.

Execute antes de enviar:

```powershell
ruff check sussurro scripts tests
python scripts/validate_all.py
pytest
```

O Ruff define o estilo do código. Não misture reformatações sem relação com a mudança e não versione ambientes virtuais, caches, modelos, builds, logs ou gravações.

Use mensagens de commit curtas no imperativo. Os prefixos `feat:`, `fix:`, `docs:`, `test:`, `refactor:` e `chore:` são os mais comuns neste repositório.
