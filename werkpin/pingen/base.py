from abc import ABC, abstractmethod
from typing import Tuple

class PinGenerator(ABC):
    __WERKZEUG_VERSIONS__ = [(-1, None, None)]

    @abstractmethod
    def get_pin_and_cookie_name(
        username: str | None,
        modname: str,
        appname: str,
        appfile: str,
        iface: str) -> Tuple[str, str]:
        pass
