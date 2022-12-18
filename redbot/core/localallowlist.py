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

from .utils.chat_formatting import (
    box,
    escape,
    humanize_list,
    humanize_number,
    humanize_timedelta,
    inline,
    pagify,
)

_ = i18n.Translator("Core", __file__)

class localallowlist(ILists):
    def __init__(self):
        pass

    async def add(self, ctx: commands.Context, *users: Union[discord.Member, int]):
        add_msg = "I cannot allow you to do this, as it would ""remove your ability to run commands, ""please ensure to add yourself to the allowlist first."
        names = [getattr(u_or_r, "name", u_or_r) for u_or_r in users]
        uids = {getattr(u_or_r, "id", u_or_r) for u_or_r in users}

        if not (ctx.guild.owner == ctx.author or await self.bot.is_owner(ctx.author)):
            current_whitelist = await self.bot.get_whitelist(ctx.guild)
            theoretical_whitelist = current_whitelist.union(uids)

            ids = {i for i in (ctx.author.id, *(getattr(ctx.author, "_roles", [])))}
            if theoretical_whitelist and ids.isdisjoint(theoretical_whitelist):
                await ctx.send(_(add_msg))

        await self.bot.add_to_whitelist(uids, guild=ctx.guild)
        if len(uids) > 1:
            await ctx.send(_("Users and/or roles have been added to the allowlist."))
        else:
            await ctx.send(_("User or role has been added to the allowlist."))

    async def list(self, ctx: commands.Context):
        curr_list = await self.bot.get_whitelist(ctx.guild)

        if not curr_list:
            await ctx.send("Server allowlist is empty.")
            return
        if len(curr_list) > 1:
            msg = _("Allowed users and/or roles:")
        else:
            msg = _("Allowed user or role:")
        for obj_id in curr_list:
            user_or_role = self.bot.get_user(obj_id) or ctx.guild.get_role(obj_id)
            if not user_or_role:
                user_or_role = _("Unknown or Deleted User/Role")
            msg += f"\n\t- {obj_id} ({user_or_role})"

        for page in pagify(msg):
            await ctx.send(box(page))

    async def remove(self, ctx: commands.Context, *users: Union[discord.Member, int]):
        rm_msg = "I cannot allow you to do this, as it would ""remove your ability to run commands."
        names = [getattr(u_or_r, "name", u_or_r) for u_or_r in users]
        uids = {getattr(u_or_r, "id", u_or_r) for u_or_r in users}

        if not (ctx.guild.owner == ctx.author or await self.bot.is_owner(ctx.author)):
            current_whitelist = await self.bot.get_whitelist(ctx.guild)  
            theoretical_whitelist = current_whitelist - uids

            ids = {i for i in (ctx.author.id, *(getattr(ctx.author, "_roles", [])))}
            if theoretical_whitelist and ids.isdisjoint(theoretical_whitelist):
                    await ctx.send(_(rm_msg))

        await self.bot.remove_from_whitelist(uids, guild=ctx.guild)
        if len(uids) > 1:
            await ctx.send(_("Users and/or roles have been removed from the server allowlist."))
        else:
            await ctx.send(_("User or role has been removed from the server allowlist."))

    async def clear(self, ctx: commands.Context):
        await self.bot.clear_whitelist(ctx.guild)
        await ctx.send(_("Server allowlist has been cleared."))