"""Garante um único Sussurro por usuário.

Duas instâncias escutam o mesmo atalho e digitam o mesmo texto ao mesmo tempo,
com as letras embaralhadas. A trava é um mutex nomeado do Windows (sem corrida
entre dois cliques rápidos); o canal local só serve para a segunda instância
pedir à primeira que mostre a janela antes de sair.
"""
from __future__ import annotations

import getpass
import logging
import sys
from collections.abc import Callable

from PySide6.QtNetwork import QLocalServer, QLocalSocket

log = logging.getLogger(__name__)

_ERROR_ALREADY_EXISTS = 183


def _key() -> str:
    try:
        user = getpass.getuser()
    except Exception:  # noqa: BLE001
        user = "default"
    return f"Sussurro-{user}"


class SingleInstance:
    def __init__(self, key: str | None = None) -> None:
        self._key = key or _key()
        self._mutex = None
        self._server: QLocalServer | None = None
        self._conns: list[QLocalSocket] = []

    def acquire(self) -> bool:
        """True se esta é a primeira instância (e passa a segurar a trava)."""
        if sys.platform != "win32":
            return True
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        handle = kernel32.CreateMutexW(None, False, f"Local\\{self._key}")
        if not handle:
            log.warning("não deu para criar o mutex de instância única")
            return True
        if kernel32.GetLastError() == _ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(ctypes.c_void_p(handle))
            return False
        self._mutex = handle  # fica aberto até o processo acabar
        return True

    def notify_running(self, timeout_ms: int = 1500) -> bool:
        """Pede à instância que já está aberta para mostrar a janela."""
        sock = QLocalSocket()
        sock.connectToServer(self._key)
        if not sock.waitForConnected(timeout_ms):
            return False
        sock.write(b"show\n")
        # disconnectFromServer só fecha depois de enviar o que está pendente;
        # sem esperar, o socket morre com a função e a mensagem se perde
        sock.disconnectFromServer()
        if sock.state() != QLocalSocket.LocalSocketState.UnconnectedState:
            sock.waitForDisconnected(timeout_ms)
        return True

    def listen(self, on_show: Callable[[], None]) -> None:
        """Atende pedidos de "show" de instâncias que tentarem abrir depois."""
        QLocalServer.removeServer(self._key)
        server = QLocalServer()
        if not server.listen(self._key):
            log.warning("canal de instância única indisponível: %s", server.errorString())
            return

        def _accept() -> None:
            while server.hasPendingConnections():
                conn = server.nextPendingConnection()
                # referência forte até desconectar: sem ela o GC do Python
                # leva o socket e o readyRead junto, e o pedido se perde
                self._conns.append(conn)
                conn.readyRead.connect(lambda c=conn: _read(c))
                conn.disconnected.connect(lambda c=conn: _drop(c))
                # o pedido pode ter chegado antes do readyRead estar ligado
                _read(conn)

        def _read(conn: QLocalSocket) -> None:
            # por linha: o pedido pode chegar em pedaços
            while conn.canReadLine():
                if bytes(conn.readLine()).strip() == b"show":
                    on_show()

        def _drop(conn: QLocalSocket) -> None:
            _read(conn)
            if conn in self._conns:
                self._conns.remove(conn)
            conn.deleteLater()

        server.newConnection.connect(_accept)
        self._server = server
