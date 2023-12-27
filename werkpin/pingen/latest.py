from __future__ import annotations
from functools import cached_property, lru_cache

import hashlib
import re
import sys
from itertools import chain
from typing import Tuple
from werkpin.filereader import FileReaderError, FileReader
from logging import getLogger

from werkpin.pingen.base import PinGenerator

logger = getLogger(__name__)

class NewestPinGenerator(PinGenerator):
    __WERKZEUG_VERSIONS__ = [
        (3, 0, None),
        (2, None, None),
        (1, None, None),
        (0, 16, None),
        (0, 15, None),
    ]

    def __init__(self, file_reader: FileReader, matched_version: Tuple) -> None:
        self.file_reader = file_reader
        if 0 <= matched_version[0] <= 1:
            self.h = hashlib.md5()
        else:
            self.h = hashlib.sha1()
    
    @lru_cache(maxsize=None)
    def uuid_node(self, iface) -> str:
        r = self.file_reader.sread(f"/sys/class/net/{iface}/address").strip()
        logger.info("Got uuid_node '%s' for iface %s", r, iface)
        return str(int(r.replace(":", ""), 16))
    
    @cached_property
    def machine_id(self) -> str | bytes | None:

        def _generate() -> str | bytes | None:
            linux = b""

            # machine-id is stable across boots, boot_id is not.
            for filename in "/etc/machine-id", "/proc/sys/kernel/random/boot_id":
                try:
                    value = self.file_reader.read(filename).strip()
                except FileReaderError:
                    continue

                if value:
                    linux += value
                    break

            # Containers share the same machine id, add some cgroup
            # information. This is used outside containers too but should be
            # relatively stable across boots.
            try:
                linux += self.file_reader.read("/proc/self/cgroup").strip().rpartition(b"/")[2]
            except FileReaderError:
                pass

            if linux:
                return linux

            raise FileReaderError("Currently only supports Linux")
            # On OS X, use ioreg to get the computer's serial number.
            try:
                # subprocess may not be available, e.g. Google App Engine
                # https://github.com/pallets/werkzeug/issues/925
                from subprocess import Popen, PIPE

                dump = Popen(
                    ["ioreg", "-c", "IOPlatformExpertDevice", "-d", "2"], stdout=PIPE
                ).communicate()[0]
                match = re.search(b'"serial-number" = <([^>]+)', dump)

                if match is not None:
                    return match.group(1)
            except (OSError, ImportError):
                pass

            # On Windows, use winreg to get the machine guid.
            if sys.platform == "win32":
                import winreg

                try:
                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        "SOFTWARE\\Microsoft\\Cryptography",
                        0,
                        winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
                    ) as rk:
                        guid: str | bytes
                        guid_type: int
                        guid, guid_type = winreg.QueryValueEx(rk, "MachineGuid")

                        if guid_type == winreg.REG_SZ:
                            return guid.encode()

                        return guid
                except OSError:
                    pass

            return None

        _machine_id = _generate()
        return _machine_id


    def get_pin_and_cookie_name(
        self,
        username: str | None,
        modname: str,
        appname: str,
        appfile: str,
        iface: str,
    ) -> tuple[str, str]:
        """Given an application object this returns a semi-stable 9 digit pin
        code and a random key.  The hope is that this is stable between
        restarts to not make debugging particularly frustrating.  If the pin
        was forcefully disabled this returns `None`.

        Second item in the resulting tuple is the cookie name for remembering.
        """
        rv = None

        # This information only exists to make the cookie unique on the
        # computer, not as a security feature.
        probably_public_bits = [
            username,
            modname,
            appname,
            appfile,
        ]

        # This information is here to make it harder for an attacker to
        # guess the cookie name.  They are unlikely to be contained anywhere
        # within the unauthenticated debug page.
        private_bits = [self.uuid_node(iface), self.machine_id]

        h = self.h
        for bit in chain(probably_public_bits, private_bits):
            if not bit:
                continue
            if isinstance(bit, str):
                bit = bit.encode()
            h.update(bit)
        
        h.update(b"cookiesalt")

        cookie_name = f"__wzd{h.hexdigest()[:20]}"

        # If we need to generate a pin we salt it a bit more so that we don't
        # end up with the same value and generate out 9 digits
        h.update(b"pinsalt")
        num = f"{int(h.hexdigest(), 16):09d}"[:9]

        # Format the pincode in groups of digits for easier remembering if
        # we don't have a result yet.
        if rv is None:
            for group_size in 5, 4, 3:
                if len(num) % group_size == 0:
                    rv = "-".join(
                        num[x : x + group_size].rjust(group_size, "0")
                        for x in range(0, len(num), group_size)
                    )
                    break
            else:
                rv = num
        return rv, cookie_name
