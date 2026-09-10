# -*- coding: utf-8 -*-
"""
DevToolboxPlugin — Ferramenta DEV exclusiva para testes de widgets
==================================================================
Playground de desenvolvimento que roda dentro do aplicativo real.
Funciona como vitrina e bancada de teste dos widgets reutilizáveis:
expõe GridRadio, GridCheckBox, GridSlider, GridDoubleSpinBox,
GridLineEdit, SimpleComboBox, GridLabel e GroupPainel/GridGroupPainel.

O botão "EXECUTAR TESTE" coleta todos os valores, simula progresso
via HUD/ProgressBar (SignalManager) e emite o resultado no Console.
Não processa arquivos — é exclusivamente uma bancada de teste.

Contratos seguidos:
  - Contrato 6: load_prefs()/save_prefs() obrigatórios
  - Contrato 11: somente widgets reutilizáveis de resources/widgets/
  - Contrato 18: ExecutionButtons via buttons_config no header do PluginPage
  - Contrato 20: HUD/ProgressBar/Console via SignalManager
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtCore import QTimer

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.grid.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.grid.GridLineEdit import GridLineEdit
from resources.widgets.grid.GridRadio import GridRadio
from resources.widgets.grid.GridSlider import GridSlider
from resources.widgets.simple.SimpleComboBox import SimpleComboBox
from utils.MessageBox import MessageBox


# ── Configs dos widgets (module-level para reuso em reset/load_prefs) ──

MODE_CONFIG: Dict[str, Dict[str, Any]] = {
    "rapido": {
        "label": "Teste Rápido",
        "description": "Executa o pipeline de teste completo",
        "default": True,
        "tooltip": "Modo padrão: todas as etapas",
    },
    "so_logs": {
        "label": "Somente Logs",
        "description": "Registra logs sem notificar no console",
        "default": False,
        "tooltip": "Útil para depurar a ferramenta",
    },
    "estresse": {
        "label": "Estresse",
        "description": "Simula cargas lentas (delays maiores)",
        "default": False,
        "tooltip": "Rota mais lenta para observar HUD/ProgressBar",
    },
}

OPTS_CONFIG: Dict[str, Dict[str, Any]] = {
    "console": {
        "label": "Console",
        "description": "Emite mensagens no ConsolePlugin",
        "default": True,
    },
    "hud": {
        "label": "HUD",
        "description": "Mostra o HUD Loader durante o teste",
        "default": True,
    },
    "toast": {
        "label": "Toast final",
        "description": "Exibe ToastNotification ao concluir",
        "default": False,
    },
    "dialog": {
        "label": "Diálogo final",
        "description": "Exibe MessageBox informativo ao concluir",
        "default": False,
    },
}

SLIDER_CONFIG: Dict[str, Dict[str, Any]] = {
    "intensidade": {
        "label": "Intensidade:",
        "default": 50,
        "min": 0,
        "max": 100,
        "step": 5,
        "suffix": "%",
        "description": "Valor numérico de teste (GridSlider)",
    },
}

NUM_CONFIG: Dict[str, Dict[str, Any]] = {
    "intervalo": {
        "label": "Intervalo (s)",
        "description": "Tempo entre etapas simuladas",
        "decimal": 1,
        "default": 0.2,
        "min": 0.1,
        "max": 5.0,
        "step": 0.1,
        "suffix": "s",
    },
    "repeticoes": {
        "label": "Repetições",
        "description": "Número inteiro de teste (QSpinBox)",
        "decimal": 0,
        "default": 5,
        "min": 1,
        "max": 100,
    },
}

TEXT_CONFIG: Dict[str, Dict[str, Any]] = {
    "titulo": {
        "label": "Título do test",
        "default": "Teste de widgets",
        "placeholder": "Nome do test...",
        "description": "Texto livre (GridLineEdit)",
    },
    "tags": {
        "label": "Tags (csv)",
        "default": "dev,test",
        "placeholder": "dev,test,ui",
        "description": "Etiquetas separadas por coma",
    },
}

COMBO_ITEMS: Dict[str, str] = {
    "info": "INFO",
    "aviso": "AVISO",
    "erro": "ERRO",
}

RESULT_CONFIG: Dict[str, Dict[str, Any]] = {
    "modo": {"label": "Modo", "value": "—"},
    "opcoes": {"label": "Opções ativas", "value": "—"},
    "intensidade": {"label": "Intensidade", "value": "—"},
    "intervalo": {"label": "Intervalo", "value": "—"},
    "repeticoes": {"label": "Repetições", "value": "—"},
    "titulo": {"label": "Título", "value": "—"},
    "severidade": {"label": "Severidade", "value": "—"},
}


class DevToolboxPlugin(BasePlugin):
    """Ferramenta DEV exclusiva: bancada de teste de widgets reutilizáveis."""

    def __init__(self, parent=None):
        super().__init__(
            tool_key=ToolKey.DEV_TOOLBOX.value,
            parent=parent,
            title="Dev Toolbox",
            buttons_config={
                "executar": {
                    "text": "EXECUTAR TESTE",
                    "callback": self._on_executar,
                    "type": "primary",
                    "description": "Coleta os widgets e simula um teste com progresso HUD/ProgressBar",
                },
                "reset": {
                    "text": "RESTAURAR",
                    "callback": self._on_reset,
                    "type": "ghost",
                    "description": "Restaura todos os widgets aos valores iniciais",
                },
            },
        )
        self.logger.info("Dev Toolbox inicializado", code="DEVTOOLBOX_READY")
        self.page.set_badge(self.page.PRONTA)

    # ── UI ────────────────────────────────────────────────────────────

    def _build_ui(self):
        super()._build_ui()

        self._grid_mode = GridRadio(MODE_CONFIG, num_columns=3)
        self._grid_opts = GridCheckBox(OPTS_CONFIG, num_columns=4)

        grp_modo = GroupPainel("Modo e Verificações")
        grp_modo.group_layout.addWidget(self._grid_mode)
        grp_modo.group_layout.addWidget(self._grid_opts)

        self._grid_slider = GridSlider(SLIDER_CONFIG)
        self._grid_num = GridDoubleSpinBox(NUM_CONFIG, columns=2)

        grp_params = GroupPainel("Parâmetros Numéricos")
        grp_params.group_layout.addWidget(self._grid_slider)
        grp_params.group_layout.addWidget(self._grid_num)

        self.main_layout.addWidget(GridGroupPainel(grp_modo, grp_params), 1)

        self._grid_text = GridLineEdit(TEXT_CONFIG)
        self._combo = SimpleComboBox(
            items=COMBO_ITEMS,
            on_item_changed=self._on_severidade_changed,
            label="Severidade:",
        )

        grp_dados = GroupPainel("Dados de Exemplo")
        grp_dados.group_layout.addWidget(self._grid_text)
        grp_dados.group_layout.addWidget(self._combo)
        self.main_layout.addWidget(grp_dados, 1)

        self._grid_result = GridLabel(RESULT_CONFIG, columns=2)

        grp_result = GroupPainel("Resultado do Último Teste")
        grp_result.group_layout.addWidget(self._grid_result)
        self.main_layout.addWidget(grp_result, 1)

    # ── Ações ─────────────────────────────────────────────────────────

    def _on_executar(self):
        self.page.buttons.set_enabled("executar", False)
        self.page.set_badge(self.page.RUNNING)
        self.statistics.start(n=0, ntype="itens")
        self.logger.info("Iniciando teste DEV", code="DEVTOOLBOX_START")

        valores = self._coletar_valores()

        SignalManager.instance().execution_started.emit(self.tool_key)
        if self._grid_opts.is_item_checked("console"):
            SignalManager.instance().console_message.emit("Iniciando teste DEV...")

        if self._grid_opts.is_item_checked("hud"):
            SignalManager.instance().hud_show.emit({"message": "Iniciando teste..."})

        pasos = [
            (15, "Validando parâmetros..."),
            (35, "Executando simulação..."),
            (65, "Processando resultados..."),
            (85, "Compilando relatório..."),
            (100, "Finalizando..."),
        ]
        delay_ms = int(self._grid_num.get("intervalo") * 1000)

        def _paso(idx: int) -> None:
            if not self.isVisible():
                return
            if idx >= len(pasos):
                self._finalizar(valores)
                return
            pct, msg = pasos[idx]
            if self._grid_opts.is_item_checked("hud"):
                SignalManager.instance().hud_update.emit(
                    {"message": msg, "progress": pct}
                )
            SignalManager.instance().progress_update.emit(pct)
            QTimer.singleShot(delay_ms, lambda: _paso(idx + 1))

        QTimer.singleShot(delay_ms, lambda: _paso(0))

    def _finalizar(self, valores: Dict[str, str]) -> None:
        """Finaliza o teste: stats, console, labels de resultado e feedback."""
        self.statistics.end()
        self.logger.info(
            "Teste DEV finalizado", code="DEVTOOLBOX_DONE", n_valores=len(valores)
        )

        if self._grid_opts.is_item_checked("console"):
            self.stats_message(n_arquivos=1, n_processed=len(valores), ntype="itens")
            SignalManager.instance().console_message.emit(
                f"Teste DEV concluído | modo={valores['modo']} | "
                f"severidade={valores['severidade']} | intensidade={valores['intensidade']}"
            )

        SignalManager.instance().hud_hide.emit()
        SignalManager.instance().progress_reset.emit()
        SignalManager.instance().execution_finished.emit(self.tool_key)

        self._grid_result.set_values(valores)

        self.page.set_badge(self.page.PRONTA)
        self.page.buttons.set_enabled("executar", True)

        if self._grid_opts.is_item_checked("toast"):
            MessageBox.show_toast("Teste DEV concluído ✔")
        if self._grid_opts.is_item_checked("dialog"):
            MessageBox.show_info(
                "Teste DEV executado com sucesso!",
                title="Dev Toolbox",
                detail="\n".join(f"{chave}: {valor}" for chave, valor in valores.items()),
            )
        self.save_prefs()

    def _on_reset(self):
        self._grid_mode.set_selected("rapido")
        self._grid_opts.set_all(
            {key: item.get("default", False) for key, item in OPTS_CONFIG.items()}
        )
        self._grid_slider.set_values(
            {key: item.get("default", 50) for key, item in SLIDER_CONFIG.items()}
        )
        self._grid_num.set_values(
            {key: item.get("default", 0) for key, item in NUM_CONFIG.items()}
        )
        self._grid_text.set_values(
            {key: item.get("default", "") for key, item in TEXT_CONFIG.items()}
        )
        self._combo.current_value = "info"
        self.logger.info(
            "Widgets restaurados aos valores iniciais", code="DEVTOOLBOX_RESET"
        )
        MessageBox.show_toast("Valores restaurados")

    def _on_severidade_changed(self, value: str) -> None:
        """Callback do SimpleComboBox — registra a mudança de severidade."""
        self.logger.info(f"Severidade alterada: {value}", code="DEVTOOLBOX_SEVERIDADE")

    # ── Coleta de valores ─────────────────────────────────────────────

    def _coletar_valores(self) -> Dict[str, str]:
        """Reúne os valores de todos os widgets como texto plano."""
        numericos = self._grid_num.values
        return {
            "modo": self._grid_mode.selected_text or "—",
            "opcoes": ", ".join(
                key for key, ativo in self._grid_opts.all.items() if ativo
            ) or "—",
            "intensidade": f"{self._grid_slider.get('intensidade')}%",
            "intervalo": f"{numericos.get('intervalo', 0):g}s",
            "repeticoes": str(numericos.get("repeticoes", 0)),
            "titulo": self._grid_text.get("titulo") or "—",
            "severidade": (self._combo.current_value or "—").upper(),
        }

    # ── Preferências (Contrato 6) ─────────────────────────────────────

    def load_prefs(self):
        modo = self.preferences.get("modo")
        if modo in self._grid_mode.keys:
            self._grid_mode.set_selected(modo)

        opcoes = self.preferences.get("opcoes")
        if opcoes:
            self._grid_opts.set_all(opcoes)

        slider = self.preferences.get("slider")
        if slider:
            self._grid_slider.set_values(slider)

        numericos = self.preferences.get("numericos")
        if numericos:
            self._grid_num.set_values(numericos)

        textos = self.preferences.get("textos")
        if textos:
            self._grid_text.set_values(textos)

        combo = self.preferences.get("combo")
        if combo in COMBO_ITEMS:
            self._combo.current_value = combo

    def save_prefs(self):
        self.preferences["modo"] = self._grid_mode.selected or ""
        self.preferences["opcoes"] = self._grid_opts.all
        self.preferences["slider"] = self._grid_slider.values
        self.preferences["numericos"] = self._grid_num.values
        self.preferences["textos"] = self._grid_text.values
        self.preferences["combo"] = self._combo.current_value or ""