# -*- coding: utf-8 -*-
"""
ThemeManager — Gerenciador central de temas
=============================================
Mantém a instância única do tema atual.
Qualquer módulo do sistema importa `ct` (current_theme) deste manager
para acessar cores, fontes, dimensões e espaçamentos centralizados.

Uso:
    from resources.styles.ThemeManager import ct
    bg = ct.BG_DARK
    btn_h = ct.BUTTON_HEIGHT

────── COMO ADICIONAR UM NOVO TEMA ────────────────────────────────
1. Crie um arquivo .py em resources/styles/ (ex: MeuTema.py)
   com uma classe que herde de BaseTheme e sobrescreva todos os tokens.

2. Importe a classe neste arquivo e registre o tema no dicionário
   THEMES abaixo, adicionando uma entrada no formato:
       "meu_tema": {
           "module":      "resources.styles.MeuTema",
           "class":       MeuTema,
           "label":       "Meu Tema",
           "description": "Descrição visual do tema",
           "author":      "Seu Nome (opcional)",
           "version":     "1.0.0 (opcional)",
       }

3. Altere CURRENT_THEME_KEY para a chave do novo tema
   (ex: CURRENT_THEME_KEY = "meu_tema").
────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from resources.styles.BaseTheme import BaseTheme
from resources.styles.DarkCharcoalTheme import DarkCharcoalTheme
from resources.styles.ZeroGrausTheme import ZeroGrausTheme
from resources.styles.BlueTheme import BlueTheme


THEMES: dict[str, dict] = {
    "dark_charcoal": {
        "module":      "resources.styles.DarkCharcoalTheme",
        "class":       DarkCharcoalTheme,
        "label":       "Dark Charcoal",
        "description": "Tema escuro minimalista com detalhes em dourado. "
                       "Profundidade via sombras, fundo preto-azulado e "
                       "acento dourado elegante.",
    },
    "zero_graus": {
        "module":      "resources.styles.ZeroGrausTheme",
        "class":       ZeroGrausTheme,
        "label":       "Zero Graus",
        "description": "Tema cristalino Ice Glass. Tons azulados profundos, "
                       "brilho frio mbar-azulado e superfícies que "
                       "simulam gelo translúcido.",
    },
    "blue_theme": {
        "module":      "resources.styles.BlueTheme",
        "class":       BlueTheme,
        "label":       "Blue Theme",
        "description": "Tema inspirado no design: "
                       "https://dribbble.com/shots/23707627-Modern-Dashboard-UI-Design. "
                       "Fundo azul-escuro profundo, cards em glassmorphism sutil, "
                       "acento azul elétrico vibrante e texto branco suave.",
    },
}

# ═══════════════════════════════════════════════════════════════════
# ALTERE AQUI O TEMA ATIVO
# ═══════════════════════════════════════════════════════════════════
# Basta mudar esta string para a chave desejada em THEMES.
# Ex: CURRENT_THEME_KEY = "zero_graus"
# ═══════════════════════════════════════════════════════════════════

CURRENT_THEME_KEY: str = "zero_graus"
CURRENT_THEME_KEY: str = "dark_charcoal"


class ThemeManager:
    """
    Gerenciador singleton de tema.
    Para alternar o tema, mude `CURRENT_THEME_KEY` para a chave
    desejada em THEMES e reinicie (ou recarregue) a UI.
    """

    _instance: ThemeManager | None = None

    def __new__(cls) -> ThemeManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._theme = cls._build_theme()
        return cls._instance

    # ── API pública ──────────────────────────────────────────────

    @property
    def theme(self) -> BaseTheme:
        """Retorna a instância do tema atual."""
        return self._theme

    @property
    def current_key(self) -> str:
        """Chave do tema ativo no momento."""
        return CURRENT_THEME_KEY

    @property
    def current_info(self) -> dict:
        """Metadados completos do tema ativo."""
        return THEMES[CURRENT_THEME_KEY]

    @classmethod
    def available_themes(cls) -> dict[str, dict]:
        """Retorna o dicionário completo de temas registrados (apenas metadados)."""
        return {
            key: {k: v for k, v in meta.items() if k != "class"}
            for key, meta in THEMES.items()
        }

    def reload_theme(self) -> None:
        """Recria a instância do tema a partir da chave configurada."""
        self._theme = self._build_theme()

    # ── Internos ─────────────────────────────────────────────────

    @staticmethod
    def _build_theme() -> BaseTheme:
        """Constrói e retorna a instância do tema apontado por CURRENT_THEME_KEY."""
        entry = THEMES.get(CURRENT_THEME_KEY)
        if entry is None:
            raise KeyError(
                f"[ThemeManager] Chave de tema '{CURRENT_THEME_KEY}' "
                f"no encontrada em THEMES. "
                f"Disponíveis: {list(THEMES.keys())}"
            )
        theme_class: type[BaseTheme] = entry["class"]
        return theme_class()


# ── Singleton pré-instanciado para importação direta ──────────────
# Uso: from resources.styles.ThemeManager import ct
ct = ThemeManager()
