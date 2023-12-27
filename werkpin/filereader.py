

from pathlib import Path
import subprocess
from functools import lru_cache, cached_property
from typing import Optional
from logging import getLogger

logger = getLogger(__name__)


class FileReaderError(Exception):
    pass

class InvalidExeSpecified(FileReaderError):
    pass

class FileReader:
    def __init__(self, exe_name:str, check_file:Optional[str] = "/etc/hosts") -> None:
        # Resolve the exe, first according to PATH, then local
        exe_fullpath = Path(exe_name)
        if not exe_fullpath.is_absolute():
            exe_fullpath = Path(subprocess.check_output(["which", exe_name]).strip().decode())
        self.exe_name = exe_fullpath
        if not self.exe_name.is_file():
            raise InvalidExeSpecified("Executable does not exist")
        if not self.exe_name.stat().st_mode & 0o111:
            raise InvalidExeSpecified("File is not executable")
        logger.info("Using filereader %s", self.exe_name)
        if check_file is not None:
            if not self._check_exe_works(check_file):
                raise InvalidExeSpecified("Your executable does not work for %s" % check_file)
            self.checked = True
        else:
            self.checked = False
    def _check_exe_works(self, check_file:str) -> bool:
        try:
            self.read(check_file)
        except FileReaderError:
            logger.warning("FileReaderError on %s", check_file)
            return False
        return True

    @lru_cache(maxsize=None)
    def read(self, path:str) -> bytes:
        try:
            output = subprocess.check_output([(self.exe_name), path])
        except subprocess.CalledProcessError as e:
            raise FileReaderError("File Error")
        return output

    def sread(self, path:str) -> str:
        return self.read(path).decode("utf-8", "replace")

    @cached_property
    def env(self):
        d = {}
        env = self.read("/proc/self/environ").replace(b"\0", b"\n").decode("utf-8", "replace")
        for line in env.split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                d[k.strip()] = v.strip()
        return d
    
    @cached_property
    def list_interfaces(self):
        ifaces =  self.sread("/proc/self/net/dev").split("\n")
        ifaces = ifaces[2:]
        ifaces = list(map(lambda x: x.split(":",1)[0].strip(), ifaces))
        return set(f for f in ifaces if f)
