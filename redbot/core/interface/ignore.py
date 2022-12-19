import io
import discord
import markdown
import random
import asyncio
import itertools
from string import ascii_letters, digits
from ..commands import CommandConverter, CogConverter

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

from ..utils.chat_formatting import (
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

class ignore(Iignore):
    def __init__(self):
        pass
    
    async def list(self, ctx: commands.Context):
        """
        List the currently ignored servers and channels.

        **Example:**
            - `[p]ignore list`
        """
        for page in pagify(await self.count_ignored(ctx)):
            await ctx.maybe_send_embed(page)
    
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
        Ignore commands in the channel, thread, or category.

        Defaults to the current thread or channel.

        Note: Owners, Admins, and those with Manage Channel permissions override ignored channels.

        **Examples:**
            - `[p]ignore channel #general` - Ignores commands in the #general channel.
            - `[p]ignore channel` - Ignores commands in the current channel.
            - `[p]ignore channel "General Channels"` - Use quotes for categories with spaces.
            - `[p]ignore channel 356236713347252226` - Also accepts IDs.

        **Arguments:**
            - `<channel>` - The channel to ignore. This can also be a thread or category channel.
        """
        if not await self.bot._ignored_cache.get_ignored_channel(channel):
            await self.bot._ignored_cache.set_ignored_channel(channel, True)
            await ctx.send(_("Channel added to ignore list."))
        else:
            await ctx.send(_("Channel already in ignore list."))
    
    async def guild(self, ctx: commands.Context):
        """
        Ignore commands in this server.

        Note: Owners, Admins, and those with Manage Server permissions override ignored servers.

        **Example:**
            - `[p]ignore server` - Ignores the current server
        """
        guild = ctx.guild
        if not await self.bot._ignored_cache.get_ignored_guild(guild):
            await self.bot._ignored_cache.set_ignored_guild(guild, True)
            await ctx.send(_("This server has been added to the ignore list."))
        else:
            await ctx.send(_("This server is already being ignored."))
            
    async def count_ignored(self, ctx: commands.Context):
        category_channels: List[discord.CategoryChannel] = []
        channels: List[Union[discord.TextChannel, discord.VoiceChannel, discord.ForumChannel]] = []
        threads: List[discord.Thread] = []
        if await self.bot._ignored_cache.get_ignored_guild(ctx.guild):
            return _("This server is currently being ignored.")
        for channel in ctx.guild.text_channels:
            if channel.category and channel.category not in category_channels:
                if await self.bot._ignored_cache.get_ignored_channel(channel.category):
                    category_channels.append(channel.category)
            if await self.bot._ignored_cache.get_ignored_channel(channel, check_category=False):
                channels.append(channel)
        for channel in ctx.guild.voice_channels:
            if channel.category and channel.category not in category_channels:
                if await self.bot._ignored_cache.get_ignored_channel(channel.category):
                    category_channels.append(channel.category)
            if await self.bot._ignored_cache.get_ignored_channel(channel, check_category=False):
                channels.append(channel)
        for channel in ctx.guild.forum_channels:
            if channel.category and channel.category not in category_channels:
                if await self.bot._ignored_cache.get_ignored_channel(channel.category):
                    category_channels.append(channel.category)
            if await self.bot._ignored_cache.get_ignored_channel(channel, check_category=False):
                channels.append(channel)
        for thread in ctx.guild.threads:
            if await self.bot._ignored_cache.get_ignored_channel(thread, check_category=False):
                threads.append(thread)

        cat_str = (
            humanize_list([c.name for c in category_channels]) if category_channels else _("None")
        )
        chan_str = humanize_list([c.mention for c in channels]) if channels else _("None")
        thread_str = humanize_list([c.mention for c in threads]) if threads else _("None")
        msg = _(
            "Currently ignored categories: {categories}\n"
            "Channels: {channels}\n"
            "Threads (excluding archived):{threads}"
        ).format(categories=cat_str, channels=chan_str, threads=thread_str)
        return msg