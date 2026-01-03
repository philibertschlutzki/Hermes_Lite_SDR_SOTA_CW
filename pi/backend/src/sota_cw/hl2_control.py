from __future__ import annotations

class HL2Control:
    """Abstraktion für HL2 Control (Frequenz/Mode).

    In dieser Repo-Version ist das bewusst ein Skeleton. Empfohlen ist die
    Einbindung einer bestehenden HL2-Python-Referenz (z. B. `hermeslite.py`).
    """

    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

    def set_frequency_hz(self, hz: int) -> None:
        # TODO: implement via HL2 UDP protocol / 3rd party library
        raise NotImplementedError("HL2 frequency control not wired yet. See third_party/README.md")

    def set_mode(self, mode: str) -> None:
        # TODO: implement via HL2 UDP protocol / 3rd party library
        raise NotImplementedError("HL2 mode control not wired yet. See third_party/README.md")
