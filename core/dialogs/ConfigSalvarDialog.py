# -*- coding: utf-8 -*-
"""
ConfigSalvarDialog — Diálogo genérico para salvar configurações em JSON.
Uso: qualquer plugin que precise persistir configurações nomeadas.

Retorna o nome do arquivo (sem .json) se salvo, ou None se cancelado.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton,
)

from utils.MessageBox import MessageBox


class ConfigSalvarDialog(QDialog):
    """
    Diálogo para salvar dados JSON em um diretório.

    Uso:
        result = ConfigSalvarDialog.exec_save(
            parent=self,
            config_dir=Path("config/data/meu_plugin"),
            data={"chave": "valor"},
            logger=self.logger,  # opcional
            console_message_fn=SignalManager.instance().console_message.emit,  # opcional
        )
        if result:
            nome, filepath = result
            print(f"Salvo como {nome}.json")
    """

    def __init__(
        self,
        parent=None,
        title: str = "Salvar Configuração",
        placeholder: str = "Ex: config_padrao",
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 140)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        label = QLabel("Nome da configuração:")
        layout.addWidget(label)

        self._edit_nome = QLineEdit()
        self._edit_nome.setPlaceholderText(placeholder)
        layout.addWidget(self._edit_nome)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        btn_salvar = QPushButton("Salvar")
        btn_salvar.clicked.connect(self.accept)
        btn_layout.addWidget(btn_salvar)
        layout.addLayout(btn_layout)

    @property
    def nome(self) -> str:
        """Nome digitado (sem extensão)."""
        return self._edit_nome.text().strip()

    @staticmethod
    def exec_save(
        config_dir: Path,
        data: Dict[str, Any],
        parent=None,
        title: str = "Salvar Configuração",
        placeholder: str = "Ex: config_padrao",
        logger: Optional[Any] = None,
        console_message_fn: Optional[Callable[[str], None]] = None,
        plugin_tag: str = "Plugin",
    ) -> Optional[str]:
        """
        Abre o diálogo e salva os dados se confirmado.

        Args:
            config_dir: Diretório onde salvar (criado automaticamente).
            data: Dicionário com os dados a persistir.
            parent: Widget pai do diálogo.
            title: Título da janela.
            placeholder: Placeholder do campo de nome.
            logger: Objeto com método .info/.error (ex: self.logger).
            console_message_fn: Função para emitir mensagens no console (ex: SignalManager).
            plugin_tag: Tag exibida nas mensagens (ex: "HotkeyPlugin").

        Returns:
            Nome do arquivo (sem .json) se salvo, None se cancelado/erro.
        """
        config_dir.mkdir(parents=True, exist_ok=True)

        dlg = ConfigSalvarDialog(
            parent=parent,
            title=title,
            placeholder=placeholder,
        )

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None

        nome = dlg.nome
        if not nome:
            MessageBox.show_warning("O nome não pode estar vazio.", title="Aviso")
            return None

        filepath = config_dir / f"{nome}.json"

        if filepath.exists():
            substituir = MessageBox.show_question(
                f"O arquivo '{nome}.json' já existe.\nDeseja substituir?",
                title="Substituir?",
            )
            if not substituir:
                return None

        data_to_save = dict(data)
        data_to_save["_saved_at"] = datetime.now().isoformat()

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

            if logger:
                logger.info("Config salva", code="CONFIG_SAVED", name=nome)
            if console_message_fn:
                console_message_fn(f"{plugin_tag} config salva: {nome}.json")

            MessageBox.show_info(
                f"Configuração '{nome}' salva com sucesso!",
                title="Salvo",
            )
            return nome

        except Exception as e:
            if logger:
                logger.error("Erro ao salvar config", code="CONFIG_SAVE_ERR", error=str(e))
            if console_message_fn:
                console_message_fn(f"{plugin_tag} erro ao salvar: {e}")
            MessageBox.show_error(f"Erro ao salvar configuração:\n{e}", title="Erro")
            return None