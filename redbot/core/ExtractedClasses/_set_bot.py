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

class _set_bot:
    async def __init__(self):
        pass
    
    async def _description(self, ctx: commands.Context, description: str = None):
        if not description:
            await ctx.bot._config.description.clear()
            ctx.bot.description = "Red V3"
            await ctx.send(_("Description reset."))
        elif len(description) > 250:  # While the limit is 256, we bold it adding characters.
            await ctx.send(
                _(
                    "This description is too long to properly display. "
                    "Please try again with below 250 characters."
                )
            )
        else:
            await ctx.bot._config.description.set(description)
            ctx.bot.description = description
            await ctx.tick()
    
    async def _avatar_remove(self, ctx: commands.Context):
        if len(ctx.message.attachments) > 0:  # Attachments take priority
            data = await ctx.message.attachments[0].read()
        elif url is not None:
            if url.startswith("<") and url.endswith(">"):
                url = url[1:-1]

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url) as r:
                        data = await r.read()
                except aiohttp.InvalidURL:
                    return await ctx.send(_("That URL is invalid."))
                except aiohttp.ClientError:
                    return await ctx.send(_("Something went wrong while trying to get the image."))
        else:
            await ctx.send_help()
            return

        try:
            async with ctx.typing():
                await ctx.bot.user.edit(avatar=data)
        except discord.HTTPException:
            await ctx.send(
                _(
                    "Failed. Remember that you can edit my avatar "
                    "up to two times a hour. The URL or attachment "
                    "must be a valid image in either JPG or PNG format."
                )
            )
        except ValueError:
            await ctx.send(_("JPG / PNG format only."))
        else:
            await ctx.send(_("Done."))
    
    async def _username(self, ctx: commands.Context, *, username: str):
        try:
            if self.bot.user.public_flags.verified_bot:
                await ctx.send(
                    _(
                        "The username of a verified bot cannot be manually changed."
                        " Please contact Discord support to change it."
                    )
                )
                return
            if len(username) > 32:
                await ctx.send(_("Failed to change name. Must be 32 characters or fewer."))
                return
            async with ctx.typing():
                await asyncio.wait_for(self._name(name=username), timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(
                _(
                    "Changing the username timed out. "
                    "Remember that you can only do it up to 2 times an hour."
                    " Use nicknames if you need frequent changes: {command}"
                ).format(command=inline(f"{ctx.clean_prefix}set bot nickname"))
            )
        except discord.HTTPException as e:
            if e.code == 50035:
                error_string = e.text.split("\n")[1]  # Remove the "Invalid Form body"
                await ctx.send(
                    _(
                        "Failed to change the username. "
                        "Discord returned the following error:\n"
                        "{error_message}"
                    ).format(error_message=inline(error_string))
                )
            else:
                log.error(
                    "Unexpected error occurred when trying to change the username.", exc_info=e
                )
                await ctx.send(_("Unexpected error occurred when trying to change the username."))
        else:
            await ctx.send(_("Done."))
    
    async def _nickname(self, ctx: commands.Context, *, nickname: str = None):
        try:
            if nickname and len(nickname) > 32:
                await ctx.send(_("Failed to change nickname. Must be 32 characters or fewer."))
                return
            await ctx.guild.me.edit(nick=nickname)
        except discord.Forbidden:
            await ctx.send(_("I lack the permissions to change my own nickname."))
        else:
            await ctx.send(_("Done."))
    
    async def _custominfo(self, ctx: commands.Context, *, text: str = None):
        if not text:
            await ctx.bot._config.custom_info.clear()
            await ctx.send(_("The custom text has been cleared."))
            return
        if len(text) <= 1024:
            await ctx.bot._config.custom_info.set(text)
            await ctx.send(_("The custom text has been set."))
            await ctx.invoke(self.info)
        else:
            await ctx.send(_("Text must be fewer than 1024 characters long."))