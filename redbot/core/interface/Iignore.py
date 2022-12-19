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

class Iignore:
    async def __init__(self):
        pass
    
    @abstractmethod
    async def list(self, ctx: commands.Context):
        pass
    
    @abstractmethod
    async def channel(
        self,
        ctx: commands.Context,
        channel: Union[
            discord.TextChannel, 
            discord.VoiceChannel, 
            discord.ForumChannel, 
            discord.CategoryChannel, 
            discord.Thread, 
        ] = commands.CurrentChannel,
    ):
        pass
    
    @abstractmethod
    async def guild(self, ctx: commands.Context):
        pass
    
    @abstractmethod
    async def count_ignored(self, ctx: commands.Context):
        pass