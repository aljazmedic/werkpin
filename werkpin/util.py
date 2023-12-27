
from typing import Tuple
from werkpin.pingen import PinGenerator
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def version_correct(match_against:Tuple, candidate:Tuple):
    logger.debug("Comparing %s to %s", match_against, candidate)
    for a, b in zip(candidate, match_against):
        if a is None: continue
        if a != b: return False
    return True

def resolve_version(version:str):
    # List PinGenerator subclasses  
    version = tuple(map(int, version.split(".")))
    candidates = PinGenerator.__subclasses__()
    # Filter out the ones that don't have a version __WERKZEUG_VERSIONS__
    logger.debug("Candidates: %s", candidates)
    for candidate in filter(lambda x: hasattr(x, "__WERKZEUG_VERSIONS__"), candidates):
        if isinstance(candidate.__WERKZEUG_VERSIONS__, tuple):
            candidate.__WERKZEUG_VERSIONS__ = [candidate.__WERKZEUG_VERSIONS__]
        for supported_version in candidate.__WERKZEUG_VERSIONS__:
            if version_correct(version, supported_version):
                logger.debug(f"Resolved version {version} to {candidate}")
                return candidate, supported_version
    raise Exception(f"No version found for Werkzeug version {version}")
