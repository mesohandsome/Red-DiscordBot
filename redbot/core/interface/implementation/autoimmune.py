import ILists
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
from ... import (
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

class autoimmune(ILists):
    def __init__(self):
        pass

    async def add(self, ctx: commands.Context, *users_or_roles: Union[discord.Member, int]):
        async with ctx.bot._config.guild(ctx.guild).autoimmune_ids() as ai_ids:
            if users_or_roles.id in ai_ids:
                return await ctx.send(_("Already added."))
            ai_ids.append(users_or_roles.id)
        await ctx.tick()

    async def list(self, ctx: commands.Context):
        ai_ids = await ctx.bot._config.guild(ctx.guild).autoimmune_ids()

        roles = {r.name for r in ctx.guild.roles if r.id in ai_ids}
        members = {str(m) for m in ctx.guild.members if m.id in ai_ids}

        output = ""
        if roles:
            output += _("Roles immune from automated moderation actions:\n")
            output += ", ".join(roles)
        if members:
            if roles:
                output += "\n"
            output += _("Members immune from automated moderation actions:\n")
            output += ", ".join(members)

        if not output:
            output = _("No immunity settings here.")

        for page in pagify(output):
            await ctx.send(page)

    async def remove(self, ctx: commands.Context, *users_or_roles: Union[discord.Member, int]):
        async with ctx.bot._config.guild(ctx.guild).autoimmune_ids() as ai_ids:
            if users_or_roles.id not in ai_ids:
                return await ctx.send(_("Not in list."))
            ai_ids.remove(users_or_roles.id)
        await ctx.tick()

    async def clear(self, ctx: commands.Context):
        pass

    async def checkimmune(self, ctx: commands.Context, *, user_or_role: Union[discord.Member, discord.Role]):
        if await ctx.bot.is_automod_immune(user_or_role):
            await ctx.send(_("They are immune."))
        else:
            await ctx.send(_("They are not immune."))