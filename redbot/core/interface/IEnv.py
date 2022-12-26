from abc import ABCMeta, abstractmethod

from typing import (
    TYPE_CHECKING,
    Union,
    Tuple,
    List,
    Optional,
    Iterable,
    Sequence,
    Dict,
    Set,
    Literal,
)

import discord
from .. import (
    __version__,
    version_info as red_version_info,
    checks,
    commands,
    errors,
    i18n,
    bank,
    modlog,
)

class IEnv:
    @abstractmethod
    async def _global():
        pass
    
    @abstractmethod
    async def _local():
        pass