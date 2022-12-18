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
from . import (
    __version__,
    version_info as red_version_info,
    checks,
    commands,
    errors,
    i18n,
    bank,
    modlog,
)

class IList:
    def __init__(self):
        pass

    @abstractmethod
    async def add(self, ctx: commands.Context, *users: Union[discord.Member, int]):
        pass

    @abstractmethod
    async def list(self, ctx: commands.Context):
        pass

    @abstractmethod
    async def remove(self, ctx: commands.Context, *users: Union[discord.Member, int]):
        pass

    @abstractmethod
    async def clear(self, ctx: commands.Context):
        pass