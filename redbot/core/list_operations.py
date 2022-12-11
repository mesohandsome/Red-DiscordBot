import asyncio
import contextlib
import datetime
import importlib
import itertools
import keyword
import logging
import io
import random
import os
import re
import sys
import traceback
from pathlib import Path
from redbot.core import data_manager
from redbot.core.utils.menus import menu
from redbot.core.utils.views import SetApiView
from redbot.core.commands import GuildConverter, RawUserIdConverter
from string import ascii_letters, digits
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

import aiohttp
import discord
from babel import Locale as BabelLocale, UnknownLocaleError
from redbot.core.data_manager import storage_type

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
from ._diagnoser import IssueDiagnoser
from .utils import AsyncIter, can_user_send_messages_in
from .utils._internal_utils import fetch_latest_red_version_info
from .utils.predicates import MessagePredicate
from .utils.chat_formatting import (
    box,
    escape,
    humanize_list,
    humanize_number,
    humanize_timedelta,
    inline,
    pagify,
)

class list_operations:
    def __init__(self):
        pass

    async def send_msg(self, ctx: commands.Context, *users: Union[discord.Member, int], msg):
        if len(users) > 1:
            await ctx.send(_(msg))
        else:
            await ctx.send(_(msg))

    def localallowlist_get_attr(self, *users_or_roles: Union[discord.Member, discord.Role, int]):
        names = [getattr(u_or_r, "name", u_or_r) for u_or_r in users_or_roles]
        uids = {getattr(u_or_r, "id", u_or_r) for u_or_r in users_or_roles}
        return names, uids

    def add_get_whitelist(self, current_whitelist, uids):
        return current_whitelist.union(uids)

    def remove_get_whitelist(self, current_whilelist, uids):
        return current_whilelist - uids

    async def localallowlist_process(self, add_or_rm, ctx: commands.Context, *users_or_roles: Union[discord.Member, discord.Role, int]):
        rm_msg = "I cannot allow you to do this, as it would ""remove your ability to run commands."
        add_msg = "I cannot allow you to do this, as it would ""remove your ability to run commands, ""please ensure to add yourself to the allowlist first."
        names, uids = self.localallowlist_get_attr(users_or_roles)

        if not (ctx.guild.owner == ctx.author or await self.bot.is_owner(ctx.author)):
            current_whitelist = await self.bot.get_whitelist(ctx.guild)
            
            if add_or_rm == 0:
                theoretical_whitelist = self.remove_get_whitelist(current_whitelist, uids)
            else:
                theoretical_whitelist = self.add_get_whitelist(current_whitelist, uids)

            ids = {i for i in (ctx.author.id, *(getattr(ctx.author, "_roles", [])))}
            if theoretical_whitelist and ids.isdisjoint(theoretical_whitelist):
                if add_or_rm == 0:
                    self.localallowlist_msg(ctx, rm_msg)
                else:
                    self.localallowlist_msg(ctx, add_msg)

        if add_or_rm == 0:
            await self.bot.remove_from_whitelist(uids, guild=ctx.guild)
            if len(uids) > 1:
                await self.localallowlist_msg(ctx, "Users and/or roles have been removed from the server allowlist.")
            else:
                await self.localallowlist_msg(ctx, "User or role has been removed from the server allowlist.")
        else:
            await self.bot.add_to_whitelist(uids, guild=ctx.guild)
            if len(uids) > 1:
                self.localallowlist_msg(ctx, "Users and/or roles have been added to the allowlist.")
            else:
                self.localallowlist_msg(ctx, "User or role has been added to the allowlist.")