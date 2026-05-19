# -*- coding: utf-8 -*-
"""
LogUtils — Logger estruturado em JSON para o Aetheris ToolBox
==============================================================
**Um unico arquivo JSON por execucao do programa.**
Todas as instancias de LogUtils escrevem no mesmo arquivo.

O arquivo e criado no primeiro `log()` / `info()` / etc. chamado.
O nome segue o formato: ``YYYYMMDD-HHMMSS_AetherisToolBox.json``

Uso:
    from core.config.LogUtils import LogUtils

    # Em uma tool registrada (com ToolKey)
    logger = LogUtils(tool="Console", class_name="ConsoleTool")

    # Em uma classe util sem ToolKey
    logger = LogUtils(tool="Utils", class_name="PreferencesHelper")

    logger.info("Sistema inicializado")
    logger.warning("Memoria baixa", code="MEM_LOW", free_mb=128)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar


class LogUtils:
    """
    Logger que escreve eventos estruturados em JSON.

    **Compartilhado**: todas as instancias de LogUtils escrevem no mesmo
    arquivo JSON da execucao atual. Cada execucao gera um novo arquivo.

    Parametros:
        tool       : Nome da ferramenta (ex: "Console", "Utils")
        class_name : Nome da classe que esta logando
        level      : Nivel minimo de log (padrao: INFO)
    """

    # ── Niveis de log ─────────────────────────────────────────────────
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    LEVEL_COLORS = {
        "DEBUG": "#9CA3AF",
        "INFO": "#10B981",
        "WARNING": "#F59E0B",
        "ERROR": "#DC2626",
        "CRITICAL": "#991B1B",
    }

    LEVEL_ORDER = [DEBUG, INFO, WARNING, ERROR, CRITICAL]

    # ── Diretorio de logs (sempre log/ na raiz do projeto) ────────────
    # core/config/LogUtils.py → parent.parent.parent = raiz do projeto
    _LOG_DIR: Path = Path(__file__).resolve().parent.parent.parent / "log"

    # ── Sessao compartilhada (class-level) ────────────────────────────
    _session_path: ClassVar[Path | None] = None
    _session_events: ClassVar[list[dict]] = []
    _session_started: ClassVar[bool] = False

    # ── Construtor ───────────────────────────────────────────────────

    def __new__(cls, *, tool: str, class_name: str, level: str | None = None) -> "LogUtils":
        instance = super().__new__(cls)
        instance._tool = tool
        instance._class_name = class_name
        instance._level = level if level is not None else cls.INFO
        return instance

    # ── Configuracao ────────────────────────────────────────────────

    def set_level(self, level: str) -> None:
        """Define o nivel minimo de log (para esta instancia)."""
        self._level = level

    @property
    def level(self) -> str:
        return self._level

    @property
    def tool(self) -> str:
        return self._tool

    @property
    def class_name(self) -> str:
        return self._class_name

    # ── API publica ─────────────────────────────────────────────────

    def log(
        self,
        msg: str,
        *,
        level: str | None = None,
        code: str | None = None,
        **data: Any,
    ) -> None:
        """
        Registra um evento de log na sessao compartilhada.

        Parametros:
            msg   : Mensagem descritiva
            level : Nivel do log (padrao: INFO)
            code  : Codigo opcional para identificar o evento (ex: "LOAD_ERR")
            **data: Dados extras (qualquer chave/valor)
        """
        level = level if level is not None else self.INFO

        if not self._allow(level):
            return

        self._ensure_session()

        event = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "tool": self._tool,
            "class": self._class_name,
            "message": msg,
        }

        if code is not None:
            event["code"] = code

        if data:
            event["data"] = data

        self._session_events.append(event)
        self._flush()

    def debug(self, msg: str, *, code: str | None = None, **data: Any) -> None:
        """Log em nivel DEBUG."""
        self.log(msg, level=self.DEBUG, code=code, **data)

    def info(self, msg: str, *, code: str | None = None, **data: Any) -> None:
        """Log em nivel INFO."""
        self.log(msg, level=self.INFO, code=code, **data)

    def warning(self, msg: str, *, code: str | None = None, **data: Any) -> None:
        """Log em nivel WARNING."""
        self.log(msg, level=self.WARNING, code=code, **data)

    def error(self, msg: str, *, code: str | None = None, **data: Any) -> None:
        """Log em nivel ERROR."""
        self.log(msg, level=self.ERROR, code=code, **data)

    def critical(self, msg: str, *, code: str | None = None, **data: Any) -> None:
        """Log em nivel CRITICAL."""
        self.log(msg, level=self.CRITICAL, code=code, **data)

    # ── Metodos internos ────────────────────────────────────────────

    def _allow(self, level: str) -> bool:
        """Verifica se o nivel e permitido pelo filtro atual."""
        if self._level not in self.LEVEL_ORDER:
            return True
        if level not in self.LEVEL_ORDER:
            return True
        return self.LEVEL_ORDER.index(level) >= self.LEVEL_ORDER.index(self._level)

    @classmethod
    def _ensure_session(cls) -> Path:
        """Garante que o arquivo da sessao foi criado (uma unica vez)."""
        if not cls._session_started:
            cls._LOG_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            cls._session_path = cls._LOG_DIR / f"{ts}_AetherisToolBox.json"
            cls._session_started = True
            cls._session_events = []
        return cls._session_path  # type: ignore

    @classmethod
    def _file(cls) -> Path:
        """Retorna o caminho do arquivo de sessao (cria se necessario)."""
        return cls._ensure_session()

    @classmethod
    def _flush(cls) -> None:
        """Escreve todos os eventos da sessao no arquivo JSON."""
        if cls._session_path is None:
            return
        with open(cls._session_path, "w", encoding="utf-8") as f:
            json.dump(cls._session_events, f, ensure_ascii=False, indent=2)

    @classmethod
    def session_file(cls) -> Path | None:
        """Retorna o caminho do arquivo de log da sessao atual."""
        return cls._session_path