---
name: Sussurro Quiet
colors:
  surface: '#111317'
  surface-dim: '#111317'
  surface-bright: '#37393e'
  surface-container-lowest: '#0c0e12'
  surface-container-low: '#1a1c20'
  surface-container: '#1e2024'
  surface-container-high: '#282a2e'
  surface-container-highest: '#333539'
  on-surface: '#e2e2e8'
  on-surface-variant: '#c7c4d7'
  inverse-surface: '#e2e2e8'
  inverse-on-surface: '#2f3035'
  outline: '#908fa0'
  outline-variant: '#464554'
  surface-tint: '#c0c1ff'
  primary: '#c0c1ff'
  on-primary: '#1000a9'
  primary-container: '#8083ff'
  on-primary-container: '#0d0096'
  inverse-primary: '#494bd6'
  secondary: '#ffb0cd'
  on-secondary: '#640039'
  secondary-container: '#aa0266'
  on-secondary-container: '#ffbad3'
  tertiary: '#c4c6cf'
  on-tertiary: '#2d3037'
  tertiary-container: '#8e9098'
  on-tertiary-container: '#272a30'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  background: '#111317'
  on-background: '#e2e2e8'
  surface-variant: '#333539'
  brand-bg: '#0B0D11'
  accent-indigo: '#6366F1'
  accent-pink: '#EC4899'
  surface-card: '#14171D'
typography:
  display:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  mono-label:
    fontFamily: Courier Prime
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 12px
  caption:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  xs: 0.25rem
  sm: 0.5rem
  md: 1rem
  lg: 1.5rem
  xl: 2rem
  window_margin: 12px
  gutter: 16px
---

## Direção visual

A interface usa fundos quase pretos, superfícies com pequena variação tonal e acentos em índigo e rosa. Os acentos ficam reservados para ações primárias, seleção e gravação ativa.

## Tipografia

Inter é a fonte da interface. Courier Prime é usada em atalhos, caminhos e informações técnicas. Textos corridos usam de 14 a 18 px; labels e legendas usam de 11 a 13 px.

## Layout

- Janelas usam margem externa de 12 px e espaçamento interno de 16 px.
- A barra lateral tem 240 px.
- O overlay mede 360 por 64 px e fica centralizado acima da barra de tarefas.
- Cards e janelas usam raio de 14 px. Botões e campos usam raio de 8 px.

## Componentes

- A marca é uma forma de onda com cinco barras e gradiente índigo para rosa.
- Atalhos aparecem em caixas de texto monoespaçado com borda discreta.
- Chips de modo usam o nome em caixa alta e a cor associada ao modo.
- O estado pronto usa um ponto verde. Durante a gravação, o ponto recebe o gradiente da marca.
- O overlay usa fundo com 92% de opacidade, borda clara de baixa opacidade e desfoque quando disponível no Windows.
- Botões primários usam o gradiente da marca. Botões secundários usam fundo transparente e borda discreta.
