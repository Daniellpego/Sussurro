"""Config TOML em %APPDATA%/Sussurro/config.toml."""
from __future__ import annotations

import tomllib
from dataclasses import asdict, dataclass
from typing import Any

from sussurro.storage.paths import config_path, write_text_atomic


@dataclass
class Config:
    # ASR
    model_size: str = "large-v3-turbo"
    compute_type: str = "int8"
    language: str = "pt"
    # quality = melhor · balanced = meio-termo · light = mais rápido
    quality_preset: str = "quality"

    # Audio
    mic_device: str | None = None  # None = default device
    sample_rate: int = 16_000

    # Desempenho / VRAM / RAM
    # False = não sobe o Ollama no boot (só quando um modo com IA for usado).
    # True = comportamento antigo: tenta abrir o Ollama junto com o Sussurro.
    ollama_autostart: bool = False
    # Quanto tempo o Qwen fica na VRAM DEPOIS de um modo com IA.
    # "0" = solta na hora (padrão: economia SEM perder qualidade do texto;
    #       o próximo Clean só demora ~20–40s a mais no load).
    # "5m" | "10m" | "30m" = mantém quente pra sequência de Clean.
    ollama_keep_alive: str = "0"
    # Ao fechar o Sussurro, descarrega modelos do Ollama da VRAM (não mata o
    # processo ollama.exe — só solta os pesos).
    ollama_unload_on_quit: bool = True
    # True = carrega o Whisper já ao ATIVAR (1ª fala rápida).
    # False = carrega só no primeiro push-to-talk (ainda mais leve).
    preload_asr: bool = False
    # libera Whisper da VRAM após ~10 min sem ditar (modelo = large-v3-turbo igual)
    unload_idle: bool = True
    # False = abre em ESPERA: quase zero VRAM até você "Ativar" na bandeja.
    # True (padrão) = já nasce armado (pronto pra Ctrl+Win assim que abre).
    start_armed: bool = True
    # Economia inteligente (sempre ligada): NÃO troca o modelo Whisper.
    # Só evita prender Qwen na VRAM quando você está em Raw / ocioso.
    # Qualidade do large-v3-turbo e dos prompts Clean = intacta.
    smart_economy: bool = True

    # Hotkey (legivel, pra UI; mudanca real requer restart por ora)
    hotkey_label: str = "Ctrl+Win"
    # Botao do mouse pra push-to-talk (alternativa ao teclado).
    # "none" | "middle" (scroll) | "x1" (lateral voltar) | "x2" (lateral avancar)
    mouse_button: str = "none"

    # Comportamento
    default_mode: str = "raw"
    auto_mode: bool = False  # escolhe o modo pelo app em foco (consciência de contexto)
    voice_commands: bool = True  # "nova linha", "novo parágrafo", pontuação por extenso
    auto_capitalization: bool = True  # capitalização inteligente do início da frase
    autostart: bool = False
    paste_after_transcribe: bool = True
    # "ctrl+v" | "shift+insert" | "type" | "auto" (tenta em cadeia)
    paste_method: str = "auto"
    # se o método preferido falhar, tenta os outros (sempre True com auto)
    paste_auto_fallback: bool = True
    show_overlay: bool = True
    # comportamento extra (config persiste; comportamento pleno em passos futuros)
    start_minimized: bool = False  # abrir minimizado na bandeja (passo 8)
    play_sound: bool = False       # sons de feedback ao gravar/concluir

    # UI
    theme: str = "system"  # "system" (segue o Windows) | "dark" | "light"
    glass: bool = False    # efeito vidro (acrílico do Windows 11) — experimental
    first_run_done: bool = False
    window_x: int | None = None
    window_y: int | None = None
    window_w: int = 780
    window_h: int = 560

    @classmethod
    def load(cls) -> Config:
        path = config_path()
        if not path.exists():
            cfg = cls()
            cfg.save()
            return cfg
        try:
            with path.open("rb") as fh:
                raw = tomllib.load(fh)
        except (OSError, tomllib.TOMLDecodeError):
            return cls()
        return cls(**{k: v for k, v in raw.items() if k in cls.__dataclass_fields__})

    @property
    def trigger_label(self) -> str:
        """Rotulo combinado teclado + mouse pra status/notificacoes."""
        from sussurro.hotkey.mouse_listener import BUTTON_LABELS

        if self.mouse_button and self.mouse_button != "none":
            mouse_lbl = BUTTON_LABELS.get(self.mouse_button, self.mouse_button)
            return f"{self.hotkey_label} ou {mouse_lbl}"
        return self.hotkey_label

    def save(self) -> None:
        data = asdict(self)
        lines: list[str] = ["# Sussurro config", ""]
        for key, value in data.items():
            lines.append(_toml_line(key, value))
        write_text_atomic(config_path(), "\n".join(lines) + "\n")


def _toml_line(key: str, value: Any) -> str:
    if value is None:
        return f"# {key} = "
    if isinstance(value, bool):
        return f"{key} = {'true' if value else 'false'}"
    if isinstance(value, (int, float)):
        return f"{key} = {value}"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'{key} = "{escaped}"'
    return f"{key} = {value!r}"
