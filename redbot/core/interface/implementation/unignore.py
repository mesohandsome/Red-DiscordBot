import io
import discord
import markdown
import random
import asyncio
import itertools
from string import ascii_letters, digits
from ...commands import CommandConverter, CogConverter

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

_entities = {
    "*": "&midast;",
    "\\": "&bsol;",
    "`": "&grave;",
    "!": "&excl;",
    "{": "&lcub;",
    "[": "&lsqb;",
    "_": "&UnderBar;",
    "(": "&lpar;",
    "#": "&num;",
    ".": "&period;",
    "+": "&plus;",
    "}": "&rcub;",
    "]": "&rsqb;",
    ")": "&rpar;",
}

from ...utils.chat_formatting import (
    box,
    escape,
    humanize_list,
    humanize_number,
    humanize_timedelta,
    inline,
    pagify,
)

_ = i18n.Translator("Core", __file__)

def entity_transformer(statement: str) -> str:
    return "".join(_entities.get(c, c) for c in statement)

import Iignore

class unignore(Iignore):
    async def __init__(self):
        pass
    
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
        """
        Remove a channel, thread, or category from the ignore list.

        Defaults to the current thread or channel.

        **Examples:**
            - `[p]unignore channel #general` - Unignores commands in the #general channel.
            - `[p]unignore channel` - Unignores commands in the current channel.
            - `[p]unignore channel "General Channels"` - Use quotes for categories with spaces.
            - `[p]unignore channel 356236713347252226` - Also accepts IDs. Use this method to unignore categories.

        **Arguments:**
            - `<channel>` - The channel to unignore. This can also be a thread or category channel.
        """
        if await self.bot._ignored_cache.get_ignored_channel(channel):
            await self.bot._ignored_cache.set_ignored_channel(channel, False)
            await ctx.send(_("Channel removed from ignore list."))
        else:
            await ctx.send(_("That channel is not in the ignore list."))
    
    async def guild(self, ctx: commands.Context):
        """
        Remove this server from the ignore list.

        **Example:**
            - `[p]unignore server` - Stops ignoring the current server
        """
        guild = ctx.message.guild
        if await self.bot._ignored_cache.get_ignored_guild(guild):
            await self.bot._ignored_cache.set_ignored_guild(guild, False)
            await ctx.send(_("This server has been removed from the ignore list."))
        else:
            await ctx.send(_("This server is not in the ignore list."))