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

class blocklist(ILists):
    def __init__(self):
        pass

    async def add(self, ctx: commands.Context, *users: Union[discord.Member, int]):
        for user in users:
            if isinstance(user, int):
                user_obj = discord.Object(id=user)
            else:
                user_obj = user
            if await ctx.bot.is_owner(user_obj):
                await ctx.send(_("You cannot add an owner to the blocklist!"))
                return

        await self.bot.add_to_blacklist(users)
        if len(users) > 1:
            await ctx.send(_("Users have been added to the blocklist."))
        else:
            await ctx.send(_("User has been added to the blocklist."))

    async def list(self, ctx: commands.Context):
        curr_list = await self.bot.get_blacklist()

        if not curr_list:
            await ctx.send("Blocklist is empty.")
            return
        if len(curr_list) > 1:
            msg = _("Users on the blocklist:")
        else:
            msg = _("User on the blocklist:")
        for user_id in curr_list:
            user = self.bot.get_user(user_id)
            if not user:
                user = _("Unknown or Deleted User")
            msg += f"\n\t- {user_id} ({user})"

        for page in pagify(msg):
            await ctx.send(box(page))

    async def remove(self, ctx: commands.Context, *users: Union[discord.Member, int]):
        await self.bot.remove_from_blacklist(users)
        await ctx.send(_("Users have been removed from the blocklist."))

    async def clear(self, ctx: commands.Context):
        await self.bot.clear_blacklist()
        await ctx.send(_("Blocklist has been cleared."))