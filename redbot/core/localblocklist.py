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

    async def add(self, ctx: commands.Context, *users_or_roles: Union[discord.Member, int]):
        for user_or_role in users_or_roles:
            uid = discord.Object(id=getattr(user_or_role, "id", user_or_role))
            if uid.id == ctx.author.id:
                await ctx.send(_("You cannot add yourself to the blocklist!"))
                return
            if uid.id == ctx.guild.owner_id and not await ctx.bot.is_owner(ctx.author):
                await ctx.send(_("You cannot add the guild owner to the blocklist!"))
                return
            if await ctx.bot.is_owner(uid):
                await ctx.send(_("You cannot add a bot owner to the blocklist!"))
                return
        await self.bot.add_to_blacklist(users_or_roles, guild=ctx.guild)

        if len(users_or_roles) > 1:
            await ctx.send(_("Users and/or roles have been added from the server blocklist."))
        else:
            await ctx.send(_("User or role has been added from the server blocklist."))

    async def list(self, ctx: commands.Context):
        curr_list = await self.bot.get_blacklist(ctx.guild)

        if not curr_list:
            await ctx.send("Server blocklist is empty.")
            return
        if len(curr_list) > 1:
            msg = _("Blocked users and/or roles:")
        else:
            msg = _("Blocked user or role:")
        for obj_id in curr_list:
            user_or_role = self.bot.get_user(obj_id) or ctx.guild.get_role(obj_id)
            if not user_or_role:
                user_or_role = _("Unknown or Deleted User/Role")
            msg += f"\n\t- {obj_id} ({user_or_role})"

        for page in pagify(msg):
            await ctx.send(box(page))

    async def remove(self, ctx: commands.Context, *users_or_roles: Union[discord.Member, int]):
        await self.bot.remove_from_blacklist(users_or_roles, guild=ctx.guild)

        if len(users_or_roles) > 1:
            await ctx.send(_("Users and/or roles have been removed from the server blocklist."))
        else:
            await ctx.send(_("User or role has been removed from the server blocklist."))

    async def clear(self, ctx: commands.Context):
        await self.bot.clear_blacklist(ctx.guild)
        await ctx.send(_("Server blocklist has been cleared."))