# Sussurro — Google Stitch UI design prompt

> **Nota de arquivo histórico:** este prompt registra uma etapa de design e pode citar componentes planejados que não fazem parte da implementação atual. Para a arquitetura vigente, consulte `docs/ARCHITECTURE.md`.

Cole o bloco abaixo no Google Stitch (em "create a new design"). É um único
prompt completo que define a identidade, os tokens, todos os componentes
e todas as 8 telas. Stitch responde melhor em inglês — esse prompt está
em inglês, mas o conteúdo da interface (microcopy) está em PT-BR.

---

## Prompt

> **Product**: Sussurro is a free, local-first Windows app that turns voice into text. Users hold a global hotkey, speak, and the transcription is pasted into whatever app is active. Everything runs offline (Whisper for ASR, a local LLM for "smart modes" like Clean / Email / Bullets / Translate). Direct competitors: Wispr Flow, SuperWhisper. The product feels premium, AI-native, and built for power users.
>
> **Aesthetic**: Dark, glassy, minimalist. Inspired by Wispr Flow, Raycast, Arc browser, and Linear. Very dark backgrounds, soft glows, indigo→pink gradient accents on interactive primary elements, generous whitespace, microinteractions. Calm, precise, intentional — NOT corporate, NOT playful.
>
> **Brand mark**: stylized audio waveform — 5 rounded vertical bars at varying heights forming a wave, rendered in the indigo→pink gradient on a rounded-square (22% radius) dark background. Sizes: 16 / 24 / 28 / 64 / 72 / 128 px.
>
> ### Design tokens
>
> Colors:
> - `bg` `#0B0D11` (near-black, slight blue undertone)
> - `surface` `#14171D` (cards, panels)
> - `surface-hover` `#1A1E26`
> - `sidebar` `#0F1217`
> - `border` `rgba(255,255,255,0.06)`
> - `border-strong` `rgba(255,255,255,0.10)`
> - `text-primary` `rgba(255,255,255,0.92)`
> - `text-secondary` `rgba(255,255,255,0.55)`
> - `text-dim` `rgba(255,255,255,0.35)`
> - `accent-a` `#6366F1` (indigo)
> - `accent-b` `#EC4899` (pink)
> - Primary gradient (brand mark, primary buttons, waveform, active states): linear `accent-a → accent-b` at 0°→90°
>
> Mode color chips:
> - raw `#94A3B8` slate · clean `#34D399` emerald · email `#60A5FA` blue · bullets `#FBBF24` amber · prompt `#A78BFA` violet · code `#F472B6` pink · translate `#2DD4BF` teal
>
> Typography: "Segoe UI Variable" → "Inter" → "Segoe UI" system fallback. Monospace: "Cascadia Mono" → "JetBrains Mono" → "Consolas". Scale (px): 11 / 12 / 13 / 14 / 16 / 18 / 22 / 28 / 36. Weights: 400 / 500 / 600 / 700. Tight tracking on large headings (-0.4 to -0.2px), wide tracking on uppercase labels (+0.5 to +1.5px).
>
> Layout: window is frameless, 920×620 default, 14 px outer radius. Custom title bar 36 px tall (left: window title, right: minimize / maximize / close, no app icon). Sidebar 220 px wide on the left, dark `sidebar` bg. Content area: 36 px horizontal padding, 28 px vertical, page title + subtitle, then stacked cards with 16 px gaps.
>
> ### Reusable components
>
> 1. **Brand mark** — 5 gradient bars on rounded-square dark bg.
> 2. **Sidebar nav item** — unicode glyph + label, 10 px padding, 8 px radius. Hover: bg `rgba(255,255,255,0.05)`. Active: bg `rgba(99,102,241,0.15)`, brighter text.
> 3. **Page title** — 22 px / 700 + 13 px secondary subtitle below.
> 4. **Card** — surface bg, 14 px radius, 1 px subtle border, 20 px padding, optional title (14 / 600) + subtitle (12 / 400).
> 5. **Keycap** — small rounded rectangle, white-on-dark, monospace 12 px, 4×10 px padding, 6 px radius. Looks like a keyboard key.
> 6. **Mode chip** — uppercase 10 px / 700 / wide tracking, 12 px radius pill, bg is mode color at 33% alpha, text white.
> 7. **Status pill** — colored dot (●) + secondary text in a thin rounded 14 px radius container. Loading: amber. Ready: emerald. Recording: gradient indigo→pink. Error: red.
> 8. **Buttons**:
>     - Primary — indigo→pink gradient, white text, 10 px radius, 9×18 px padding, 13 / 600.
>     - Secondary — surface-hover bg, primary text, 1 px border, 10 px radius, 8×14 px.
>     - Ghost — transparent, secondary text, no border, 6×10 px.
> 9. **Floating overlay (pill)** — frameless 360×64 px, 32 px radius (full pill), positioned centered horizontally at 96 px from screen bottom. Background `#14161A` at 92% alpha + 11% white inner border + soft outer shadow. Contents (left → right): mode chip, animated waveform OR spinner dots (swaps by state), timer "0:03" (monospace).
> 10. **Custom checkbox** — 18×18 px, 5 px radius. Unchecked: `surface-hover` bg, 1 px `border-strong`. Checked: indigo→pink gradient bg, no border, white check mark.
> 11. **Tray icon menu** — right-click menu styled to match dark theme. `surface` bg, 1 px border, 8 px radius. Hover indigo-tint.
>
> ### Screens to generate
>
> **1. Onboarding (first-run wizard, 3 steps)**
> Centered modal-style on dark bg, no sidebar. Progress dots at top.
> - Step 1: large brand mark, headline "Bem-vindo ao Sussurro" (28 / 700), 2-line body "fala e cola em qualquer app. 100% local — nada sai do seu PC." Primary button "Começar".
> - Step 2: microphone test. Dropdown listing mic devices. Below: a big circle "Diga olá" pulsing softly. Once tapped, it records 3 s, shows the waveform animation, then shows the recognized text. Primary button "Tudo certo" enables after first test.
> - Step 3: hotkey explainer. Two large keycaps "Ctrl + Win" centered. Body: "Mantenha pressionado, fale, solte. O texto aparece no app ativo." Primary button "Pronto".
>
> **2. Home (default page on every launch)**
> Sidebar on left (full nav). Content area:
> - Status pill top-left ("● pronto · Ctrl+Win" in emerald)
> - Vertical hero centered: "Pressione e segure" (28 / 700), keycaps row "Ctrl + Win" (large), caption "para falar e transcrever no app ativo" (13 / secondary)
> - Below: card titled "Transcrições recentes" with the 3 latest items. Each item is a small inner card: meta line (time · mode), then the transcribed text.
>
> **3. Histórico (full log)**
> - Header row: search input (flexible) + secondary button "limpar tudo"
> - Scrollable vertical list of cards. Each card: top row meta (date · time · duration, mode chip, "copiar" ghost button right-aligned), then the full transcribed text in 13 px primary, selectable.
> - Card hover: border opacity 6% → 10%.
>
> **4. Modos (7 LLM processing modes)**
> Vertical list of cards. Each card has the mode chip on the top-left, a one-line description in 13 px secondary, and a "Editar prompt" ghost button on the right. The 7 modes (in order): Raw, Clean, Email, Bullets, Prompt, Code, Translate. Show one card in an expanded/editing state: textarea revealed below the description with the current prompt, "Salvar" primary button + "Restaurar padrão" ghost button row at the bottom.
>
> **5. Ajustes**
> Stack of cards on the page:
> - "Áudio": one row "Microfone" + dropdown
> - "Transcrição": three rows — "Idioma" dropdown (PT-BR / English / Detectar automático), "Modo padrão" dropdown, "Modelo" read-only keycap-style label "large-v3"
> - "Atalho": "Push-to-talk" + keycap "Ctrl+Win" + dim caption "customização em breve"
> - "Comportamento": three checkbox rows — "Colar texto automaticamente", "Mostrar overlay flutuante", "Iniciar com o Windows", followed by a dim caption about autostart
> - "Avançado" (collapsible, default closed): "Limpar histórico", "Resetar configuração", "Abrir pasta de logs"
>
> **6. Sobre**
> Centered hero: brand mark 72 px, "Sussurro" (28 / 700), "versão 0.1" (12 / dim). Two cards stacked below:
> - "Sistema": list of monospace 12 px secondary lines — "GPU: NVIDIA RTX 4070 Ti, 12 GB", "Python: 3.11.9", "Sistema: Windows 11", "Modelo: large-v3 (int8_float16)", "LLM: Qwen 2.5 7B Q5_K_M"
> - "Créditos": paragraph in 13 px secondary: "Construído com PySide6, faster-whisper (CTranslate2) e Silero VAD. Tudo roda localmente — nenhum áudio sai do seu PC." Optional link row at the bottom (GitHub, Whisper, CTranslate2).
>
> **7. Floating overlay — 3 states side by side**
> Show three pill snapshots in a row, centered on a dark canvas (no window chrome), to communicate the recording lifecycle:
> - **Recording**: chip "RAW" left, 18 animated gradient bars center, timer "0:03" mono right
> - **Transcribing**: chip "RAW" left, 3 pulsing gradient dots center, label "transcrevendo" right (no timer)
> - **Done**: chip "RAW" left, small emerald check center, label "ok" right
>
> **8. System tray menu**
> Show the Windows tray area at the bottom right of the screen with the brand mark icon, and the right-click menu open above it. Menu (top to bottom): "Abrir Sussurro" (bold default item), divider, "Pausar transcrição" (checkable with custom check style), divider, "Sair". Match dark theme — `surface` bg, 1 px border, 8 px radius, hover indigo-tint.
>
> ### Microinteractions to imply via states
>
> - Hover on cards: border opacity 6% → 10%
> - Hover on primary button: gradient shifts 6 px down (very subtle)
> - Recording overlay fade-in: 180 ms cubic-out, scale 0.96 → 1.0
> - Recording → transcribing: waveform crossfades into spinner dots
> - Done state holds 700 ms then fades out over 200 ms
>
> ### Constraints
>
> - All screens use the same color tokens — no off-palette colors
> - Microcopy in Portuguese-BR, lowercase for secondary labels, no exclamation marks, no emojis in UI text
> - Generous whitespace; never cramped
> - No drop shadows except a subtle one under the floating overlay pill
> - No icons from icon libraries — use unicode glyphs (◉ ≡ ✦ ⚙ ⓘ ●) where icons are needed
> - All buttons, cards, and interactive elements have visible focus / hover states implied
> - Design at 1× DPI for 1080p, but assume scalable (vector / px tokens)

---

## Como usar

1. Abra https://stitch.withgoogle.com
2. Cole o prompt inteiro (do "**Product**" até "**Constraints**")
3. Stitch vai gerar primeiro um mood / componentes — refine se precisar
4. Pra gerar cada tela individualmente, copie só a seção "Screens to generate" da tela que você quer (ex: "**2. Home**") e use como prompt focado
5. Exporte os mocks (PNG / Figma link) e me manda — eu replico em PySide6 ajustando o que estiver diferente do código atual

Dica: pra um único arquivo Figma com tudo, peça pro Stitch: *"render all 8 screens in a single Figma frame, 1440px wide, arranged in a 4×2 grid with labels above each"*.
