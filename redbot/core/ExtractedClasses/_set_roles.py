import io
import discord
import markdown
import random
import asyncio
from string import ascii_letters, digits
from redbot.core.utils.views import SetApiView
from babel import Locale as BabelLocale, UnknownLocaleError

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
TokenConverter = commands.get_dict_converter(delims=[" ", ",", ";"])

def entity_transformer(statement: str) -> str:
    return "".join(_entities.get(c, c) for c in statement)

class _set_roles:
    async def __init__(self, ctx: commands.Context):
        pass
    
    async def _add_admin_role(self, ctx: commands.Context, *, role: discord.Role):
        async with ctx.bot._config.guild(ctx.guild).admin_role() as roles:
            if role.id in roles:
                return await ctx.send(_("This role is already an admin role."))
            roles.append(role.id)
        await ctx.send(_("That role is now considered an admin role."))
        
    async def _add_mod_role(self, ctx: commands.Context, *, role: discord.Role):
        async with ctx.bot._config.guild(ctx.guild).mod_role() as roles:
            if role.id in roles:
                return await ctx.send(_("This role is already a mod role."))
            roles.append(role.id)
        await ctx.send(_("That role is now considered a mod role."))
        
    async def _remove_admin_role(self, ctx: commands.Context, *, role: discord.Role):
        async with ctx.bot._config.guild(ctx.guild).admin_role() as roles:
            if role.id not in roles:
                return await ctx.send(_("That role was not an admin role to begin with."))
            roles.remove(role.id)
        await ctx.send(_("That role is no longer considered an admin role."))
        
    async def _remove_mod_role(self, ctx: commands.Context, *, role: discord.Role):
        async with ctx.bot._config.guild(ctx.guild).mod_role() as roles:
            if role.id not in roles:
                return await ctx.send(_("That role was not a mod role to begin with."))
            roles.remove(role.id)
        await ctx.send(_("That role is no longer considered a mod role."))