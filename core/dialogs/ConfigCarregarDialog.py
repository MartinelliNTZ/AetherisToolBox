# -*- coding: utf-8 -*-
"""
ConfigCarregarDialog — Diálogo genérico para carregar configurações JSON.
Uso: qualquer plugin que precise carregar configurações nomeadas de um diretório.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QPushButton,
)

from utils.MessageBox import MessageBox


class ConfigCarregarDialog(QDialog):
    """
    Diálogo para selecionar e carregar um arquivo JSON de configuração.

    Uso:
        data = ConfigCarregarDialog.exec_load(
            parent=self,
            config_dir=Path("config/data/meu_plugin"),
            logger=self.logger,
            console_message_fn=SignalManager.instance().console_message.emit,
            plugin_tag="MeuPlugin",
        )
        if data:
            print(f"Carregado: {data}")
    """

    def __init__(
        self,
        json_files: List[Path],
        parent=None,
        title: str = "Carregar Configuração",
        prompt: str = "Selecione uma configuração para carregar:",
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(500, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        label = QLabel(prompt)
        layout.addWidget(label)

        self._list = QListWidget()
        for fp in json_files:
            nome = fp.stem
            mtime = datetime.fromtimestamp(fp.stat().st_mtime)
            data_str = mtime.strftime("%d/%m/%Y %H:%M:%S")
            self._list.addItem(f"{nome}  [{data_str}]")
        layout.addWidget(self._list)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)
        btn_carregar = QPushButton("Carregar")
        btn_carregar.clicked.connect(self.accept)
        btn_layout.addWidget(btn_carregar)
        layout.addLayout(btn_layout)

        self._json_files = json_files

    @property
    def selected_path(self) -> Optional[Path]:
        """Retorna o Path do arquivo selecionado, ou None."""
        row = self._list.currentRow()
        if row < 0 or row >= len(self._json_files):
            return None
        return self._json_files[row]

    @staticmethod
    def exec_load(
        config_dir: Path,
        parent=None,
        title: str = "Carregar Configuração",
        prompt: str = "Selecione uma configuração para carregar:",
        logger: Optional[Any] = None,
        console_message_fn: Optional[Callable[[str], None]] = None,
        plugin_tag: str = "Plugin",
    ) -> Optional[Dict[str, Any]]:
        """
        Abre o diálogo e carrega os dados se confirmado.

        Args:
            config_dir: Diretório onde buscar arquivos .json.
            parent: Widget pai do diálogo.
            title: Título da janela.
            prompt: Texto do label.
            logger: Objeto com método .info/.error.
            console_message_fn: Função para emitir mensagens no console.
            plugin_tag: Tag para mensagens.

        Returns:
            Dicionário com os dados carregados, ou None se cancelado/erro.
        """
        config_dir.mkdir(parents=True, exist_ok=True)
        json_files = sorted(config_dir.glob("*.json"))

        if not json_files:
            MessageBox.show_info(
                "Nenhuma configuração salva encontrada.\n"
                "Use 'SALVAR CONFIG' para criar uma.",
                title="Nenhuma Config",
            )
            return None

        dlg = ConfigCarregarDialog(
            json_files=json_files,
            parent=parent,
            title=title,
            prompt=prompt,
        )

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None

        selected_file = dlg.selected_path
        if selected_file is None:
            return None

        try:
            with open(selected_file, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)

            if logger:
                logger.info("Config carregada", code="CONFIG_LOADED", name=selected_file.stem)
            if console_message_fn:
                console_message_fn(
                    f"{plugin_tag} config carregada: {selected_file.stem}.json"
                )

            MessageBox.show_info(
                f"Configuração '{selected_file.stem}' carregada com sucesso!",
                title="Carregado",
            )
            return data

        except Exception as e:
            if logger:
                logger.error("Erro ao carregar config", code="CONFIG_LOAD_ERR", error=str(e))
            if console_message_fn:
                console_message_fn(f"{plugin_tag} erro ao carregar: {e}")
            MessageBox.show_error(f"Erro ao carregar configuração:\n{e}", title="Erro")
            return None