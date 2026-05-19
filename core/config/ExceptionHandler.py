# -*- coding: utf-8 -*-
"""
ExceptionHandler — Sistema global de captura de exceções
=========================================================
Previne crashes não tratados instalando hooks em três níveis:

1. **sys.excepthook** — Captura exceções Python não tratadas
2. **Qt message handler** — Captura warnings/errors do Qt (qInstallMessageHandler)
3. **Decorator @safe_exec** — Protege callbacks específicos contra crash

Todas as exceções são:
  - Logadas via LogUtils com traceback completo
  - Exibidas em um QMessageBox amigável (quando possível)
  - Impedidas de propagar (evita crash) sempre que seguro

Uso:
    from core.config.ExceptionHandler import ExceptionHandler

    # Instala os hooks globais (chamar uma vez no startup)
    ExceptionHandler.install()

    # Decorator para proteger callbacks específicos
    @ExceptionHandler.safe_exec
    def meu_callback():
        ...
"""

from __future__ import annotations

import sys
import traceback
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication

from core.config.LogUtils import LogUtils
from utils.MessageBox import MessageBox

F = TypeVar("F", bound=Callable[..., Any])

# ── Logger base para o sistema de exceções ────────────────────────
_logger = LogUtils(tool="System", class_name="ExceptionHandler")


class ExceptionHandler:
    """
    Gerenciador global de exceções não tratadas.

    Métodos de classe:
        install()           — Instala todos os hooks
        uninstall()         — Remove os hooks (para testes)
        safe_exec(func)     — Decorator que envolve função em try/except

    Atributos de classe:
        show_dialog         — Se True (padrão), exibe QMessageBox no excepthook
        last_exception      — Armazena a última exceção (evita loop recursivo)
    """

    # ── Controle de estado ───────────────────────────────────────────
    _installed: bool = False
    _original_excepthook: Any = None
    _original_qt_handler: Any = None
    _recursion_guard: bool = False
    _systray_active: bool = False  # reservado para futura notificação systray

    # ── Configuração ─────────────────────────────────────────────────
    show_dialog: bool = True
    """Se True, exibe QMessageBox com detalhes do erro no excepthook."""

    max_traceback_lines: int = 50
    """Máximo de linhas do traceback para exibir no diálogo."""

    # ═════════════════════════════════════════════════════════════════
    # Instalação dos hooks
    # ═════════════════════════════════════════════════════════════════

    @classmethod
    def install(cls) -> None:
        """
        Instala todos os hooks de captura de exceção.

        Deve ser chamado UMA VEZ, o mais cedo possível no startup,
        de preferência antes de criar a QApplication.
        """
        if cls._installed:
            return

        _logger.info(
            "Instalando hooks globais de exceção",
            code="EXC_HOOK_INSTALL",
        )

        # 1. Hook do Python (sys.excepthook)
        cls._original_excepthook = sys.excepthook
        sys.excepthook = cls._python_excepthook

        # 2. Hook do Qt (qInstallMessageHandler)
        try:
            from PySide6.QtCore import qInstallMessageHandler
            cls._original_qt_handler = qInstallMessageHandler(None)
            qInstallMessageHandler(cls._qt_message_handler)
        except Exception as exc:
            _logger.warning(
                "Falha ao instalar Qt message handler",
                code="QT_HOOK_FAIL",
                error=str(exc),
            )

        cls._installed = True
        _logger.info("Hooks de exceção instalados com sucesso", code="EXC_HOOK_OK")

    @classmethod
    def uninstall(cls) -> None:
        """Remove os hooks instalados (útil para testes)."""
        if not cls._installed:
            return

        # Restaura hook Python
        if cls._original_excepthook is not None:
            sys.excepthook = cls._original_excepthook

        # Restaura hook Qt
        if cls._original_qt_handler is not None:
            try:
                from PySide6.QtCore import qInstallMessageHandler
                qInstallMessageHandler(cls._original_qt_handler)
            except Exception:
                pass

        cls._installed = False
        _logger.info("Hooks de exceção removidos", code="EXC_HOOK_REMOVED")

    # ═════════════════════════════════════════════════════════════════
    # sys.excepthook — Exceções Python não tratadas
    # ═════════════════════════════════════════════════════════════════

    @classmethod
    def _python_excepthook(
        cls,
        exc_type: type,
        exc_value: BaseException,
        exc_tb: Optional[Any],
    ) -> None:
        """
        Captura qualquer exceção não tratada no Python.

        Etapas:
            1. Prevenção de loop recursivo
            2. Log do erro com traceback completo
            3. Exibição de diálogo amigável (se show_dialog e QApplication ativa)
            4. Tentativa de manter a aplicação viva
        """
        # ── Prevenção de loop recursivo ──────────────────────────────
        if cls._recursion_guard:
            # Já estamos processando uma exceção. Escreve direto no stderr
            # para evitar loop infinito.
            import io
            buf = io.StringIO()
            if exc_tb:
                traceback.print_exception(exc_type, exc_value, exc_tb, file=buf)
            else:
                traceback.print_exception(exc_type, exc_value, None, file=buf)
            print(f"[EXCEPTION GUARD] {buf.getvalue()}", file=sys.stderr)
            return

        cls._recursion_guard = True

        try:
            # ── Extrai traceback ─────────────────────────────────────
            tb_lines: list[str] = []
            if exc_tb:
                tb_lines = traceback.format_tb(exc_tb)
            tb_text = "".join(tb_lines)

            # Último frame (onde o erro ocorreu)
            last_frame_info = ""
            if tb_lines:
                last_line = tb_lines[-1].strip() if tb_lines else ""
                last_frame_info = last_line

            # ── Loga o erro completo ─────────────────────────────────
            _logger.critical(
                f"Exceção não tratada: {exc_type.__name__}: {exc_value}",
                code="UNHANDLED_EXCEPTION",
                exception_type=exc_type.__name__,
                exception_message=str(exc_value),
                traceback=tb_text,
                last_frame=last_frame_info,
            )

            # Também loga via logger global do módulo
            _log_to_all_loggers(
                level="CRITICAL",
                msg=f"EXCEÇÃO NÃO TRATADA: {exc_type.__name__}: {exc_value}",
                traceback=tb_text,
            )

            # ── Exibe diálogo amigável ───────────────────────────────
            if cls.show_dialog:
                cls._show_error_dialog(
                    title="Erro Inesperado",
                    message=(
                        f"Ocorreu um erro inesperado no Aetheris ToolBox.\n\n"
                        f"Tipo: {exc_type.__name__}\n"
                        f"Detalhes: {exc_value}\n\n"
                        f"O erro foi registrado no arquivo de log.\n"
                        f"O programa tentará continuar funcionando."
                    ),
                    detailed_text=(
                        f"Exceção: {exc_type.__name__}: {exc_value}\n\n"
                        f"Traceback:\n{tb_text}"
                    ),
                )

        except Exception as inner_exc:
            # Falha ao processar a exceção — escreve no stderr como fallback
            print(
                f"[EXCEPTION HANDLER ERROR] Falha ao processar exceção: "
                f"{inner_exc}",
                file=sys.stderr,
            )
            print(
                f"[EXCEPTION HANDLER ERROR] Exceção original: "
                f"{exc_type.__name__}: {exc_value}",
                file=sys.stderr,
            )
            if exc_tb:
                traceback.print_exception(exc_type, exc_value, exc_tb)
        finally:
            cls._recursion_guard = False

    # ═════════════════════════════════════════════════════════════════
    # Qt Message Handler — Warnings/Errors do Qt
    # ═════════════════════════════════════════════════════════════════

    @classmethod
    def _qt_message_handler(
        cls,
        msg_type: Any,
        context: Any,
        message: str,
    ) -> None:
        """
        Captura mensagens do Qt (qInstallMessageHandler).

            msg_type: QtMsgType (QtDebugMsg, QtWarningMsg, QtCriticalMsg, QtFatalMsg)
            context: QMessageLogContext
            message: str — mensagem original
        """
        from PySide6.QtCore import QtMsgType

        # Mapeia tipo Qt para level do LogUtils
        type_map = {
            QtMsgType.QtDebugMsg: "DEBUG",
            QtMsgType.QtInfoMsg: "INFO",
            QtMsgType.QtWarningMsg: "WARNING",
            QtMsgType.QtCriticalMsg: "ERROR",
            QtMsgType.QtFatalMsg: "CRITICAL",
        }
        level = type_map.get(msg_type, "WARNING")

        # Extrai informações de contexto (arquivo, linha, função)
        ctx_file = ""
        ctx_line = 0
        ctx_function = ""
        try:
            ctx_file = context.file or ""
            ctx_line = context.line or 0
            ctx_function = context.function or ""
        except Exception:
            pass

        # Ignora warnings de fontes conhecidas (ruído)
        if cls._is_qt_noise(level, message):
            return

        # Loga a mensagem Qt
        _qt_logger = LogUtils(tool="Qt", class_name="QtMessageHandler")
        log_method = getattr(_qt_logger, level.lower(), _qt_logger.warning)
        log_method(
            message,
            code=f"QT_{level}",
            qt_file=ctx_file,
            qt_line=ctx_line,
            qt_function=ctx_function,
        )

        # Se for QtFatalMsg, exibe diálogo (mas não deixa o Qt abortar)
        if msg_type == QtMsgType.QtFatalMsg:
            cls._show_error_dialog(
                title="Erro Interno (Qt)",
                message=(
                    f"O sistema gráfico reportou um erro grave.\n\n"
                    f"{message}\n\n"
                    f"Tente salvar seu trabalho e reiniciar a aplicação."
                ),
                detailed_text=(
                    f"Qt Fatal Error\n"
                    f"Arquivo: {ctx_file}\n"
                    f"Linha: {ctx_line}\n"
                    f"Função: {ctx_function}\n\n"
                    f"Mensagem: {message}"
                ),
            )

    @classmethod
    def _is_qt_noise(cls, level: str, message: str) -> bool:
        """
        Verifica se a mensagem Qt é ruído conhecido que não merece log.

        Retorna True se a mensagem deve ser suprimida.
        """
        # Ruídos comuns do Qt/PySide6
        noise_patterns = [
            "libpng warning",
            "QFont::setPixelSize",
            "setFeature is not available",
            "Window surface was destroyed",
            "does not have a composition",
        ]
        for pattern in noise_patterns:
            if pattern.lower() in message.lower():
                return True
        return False

    # ═════════════════════════════════════════════════════════════════
    # Decorator @safe_exec
    # ═════════════════════════════════════════════════════════════════

    @classmethod
    def safe_exec(cls, func: F) -> F:
        """
        Decorator que envolve a função em try/except, logando
        qualquer exceção e impedindo que ela se propague.

        Uso:
            @ExceptionHandler.safe_exec
            def meu_callback():
                ...

        Em slots do Qt conectados via Signal, use safe_exec para
        evitar que uma exceção derrube o event loop.
        """
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                tb_text = "".join(traceback.format_exc())
                _logger.error(
                    f"Exceção capturada por safe_exec em {func.__name__}: {exc}",
                    code="SAFE_EXEC_CAUGHT",
                    function=func.__name__,
                    module=getattr(func, "__module__", ""),
                    error=str(exc),
                    traceback=tb_text,
                )

                # Se for um slot Qt e show_dialog, exibe alerta
                if cls.show_dialog and QApplication.instance() is not None:
                    # Usa QTimer.singleShot para não bloquear o event loop
                    QTimer.singleShot(0, lambda: cls._show_error_dialog(
                        title="Erro em Operação",
                        message=(
                            f"Ocorreu um erro ao executar '{func.__name__}'.\n\n"
                            f"{exc}\n\n"
                            f"A operação foi cancelada, mas o programa continua."
                        ),
                        detailed_text=tb_text,
                    ))
                return None
        return wrapper  # type: ignore[return-value]

    # ═════════════════════════════════════════════════════════════════
    # Decorator @safe_slot — para slots do Qt
    # ═════════════════════════════════════════════════════════════════

    @classmethod
    def safe_slot(cls, func: F) -> F:
        """
        Decorator específico para slots do Qt.

        Diferença do safe_exec: também captura BaseException (ex: SystemExit,
        KeyboardInterrupt) e previne que o slot pare o event loop.

        Uso:
            @ExceptionHandler.safe_slot
            def on_click(self):
                ...
        """
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except (Exception, SystemExit, KeyboardInterrupt) as exc:
                tb_text = "".join(traceback.format_exc())
                _logger.error(
                    f"Exceção capturada por safe_slot em {func.__name__}: {exc}",
                    code="SAFE_SLOT_CAUGHT",
                    function=func.__name__,
                    module=getattr(func, "__module__", ""),
                    error=str(exc),
                    traceback=tb_text,
                )
                return None
        return wrapper  # type: ignore[return-value]

    # ═════════════════════════════════════════════════════════════════
    # Diálogo de erro amigável
    # ═════════════════════════════════════════════════════════════════

    @classmethod
    def _show_error_dialog(
        cls,
        title: str,
        message: str,
        detailed_text: str = "",
    ) -> None:
        """
        Exibe um QMessageBox com detalhes do erro via MessageBox centralizado.

        Tenta obter a janela ativa como parent. Se não houver
        QApplication, apenas loga.
        """
        app = QApplication.instance()
        if app is None:
            # Sem GUI ativa — apenas loga (já foi logado antes)
            return

        try:
            # Usa o MessageBox centralizado
            MessageBox.show_error(
                text=message,
                title=title,
                detail=detailed_text,
            )
        except Exception as dlg_exc:
            # Falha ao exibir diálogo — loga e segue
            _logger.error(
                "Falha ao exibir diálogo de erro",
                code="DLG_FAIL",
                dialog_error=str(dlg_exc),
            )

    # ═════════════════════════════════════════════════════════════════
    # Utilitário: protege execução de um bloco
    # ═════════════════════════════════════════════════════════════════

    @staticmethod
    def try_exec(
        func: Callable[..., Any],
        *args: Any,
        fallback_return: Any = None,
        log_as_warning: bool = False,
        **kwargs: Any,
    ) -> Any:
        """
        Executa uma função capturando qualquer exceção.

        Útil para chamadas únicas onde você não quer usar decorator.

        Parâmetros:
            func            : Função a executar
            fallback_return : Valor retornado em caso de erro
            log_as_warning  : Se True, loga como WARNING em vez de ERROR

        Retorna:
            Valor retornado por func, ou fallback_return em caso de erro.
        """
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            tb_text = "".join(traceback.format_exc())
            log_method = _logger.warning if log_as_warning else _logger.error
            log_method(
                f"Exceção em try_exec ({func.__name__}): {exc}",
                code="TRY_EXEC_CAUGHT",
                function=func.__name__,
                error=str(exc),
                traceback=tb_text if not log_as_warning else "",
            )
            return fallback_return

    # ═════════════════════════════════════════════════════════════════
    # Relatório de erros (pode ser chamado externamente)
    # ═════════════════════════════════════════════════════════════════

    @staticmethod
    def report_error(
        message: str,
        exc_info: Optional[Any] = None,
        code: str = "MANUAL_REPORT",
        **extra: Any,
    ) -> None:
        """
        Registra manualmente um erro no sistema de logs.

        Útil para pontos onde você quer capturar e reportar
        sem usar os hooks automáticos.

        Parâmetros:
            message  : Mensagem descritiva
            exc_info : Tupla (type, value, traceback) ou None (usa sys.exc_info())
            code     : Código opcional do evento
            **extra  : Dados extras para o log
        """
        import sys as _sys

        if exc_info is None:
            exc_info = _sys.exc_info()

        tb_text = ""
        if exc_info and exc_info[2]:
            tb_lines = traceback.format_tb(exc_info[2])
            tb_text = "".join(tb_lines)

        _logger.error(
            message,
            code=code,
            traceback=tb_text,
            **extra,
        )


# ═══════════════════════════════════════════════════════════════════════
# Função auxiliar: loga em múltiplos loggers
# ═══════════════════════════════════════════════════════════════════════

def _log_to_all_loggers(
    level: str,
    msg: str,
    **extra: Any,
) -> None:
    """
    Garante que mensagens críticas sejam registradas em pelo menos
    um logger do sistema.
    """
    try:
        # Tenta logar no LogUtils principal
        logger = LogUtils(tool="System", class_name="ExceptionHandler")
        getattr(logger, level.lower(), logger.info)(msg, **extra)
    except Exception:
        # Fallback: escreve direto no stderr
        print(f"[{level}] {msg}", file=sys.stderr)
        if extra:
            print(f"  Extra: {extra}", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════════════
# Atalho: decorator safe_exec como função autônoma
# ═══════════════════════════════════════════════════════════════════════

def safe_exec(func: F) -> F:
    """
    Atalho para ExceptionHandler.safe_exec.

    Uso:
        from core.config.ExceptionHandler import safe_exec

        @safe_exec
        def minha_func():
            ...
    """
    return ExceptionHandler.safe_exec(func)


def safe_slot(func: F) -> F:
    """
    Atalho para ExceptionHandler.safe_slot.

    Uso:
        from core.config.ExceptionHandler import safe_slot

        @safe_slot
        def meu_slot():
            ...
    """
    return ExceptionHandler.safe_slot(func)