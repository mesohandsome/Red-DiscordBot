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
TokenConverter = commands.get_dict_converter(delims=[" ", ",", ";"])

def entity_transformer(statement: str) -> str:
    return "".join(_entities.get(c, c) for c in statement)

import IEnv

class _set_locale(IEnv):
    async def __init__(self, ctx: commands.Context, language_code: str):
        if ctx.guild is None:
            await ctx.send_help()
            return
        await ctx.invoke(self._set_locale_local, language_code)
        
    async def _global(self, ctx: commands.Context, language_code: str):
        try:
            locale = BabelLocale.parse(language_code, sep="-")
        except (ValueError, UnknownLocaleError):
            await ctx.send(_("Invalid language code. Use format: `en-US`"))
            return
        if locale.territory is None:
            await ctx.send(
                _("Invalid format - language code has to include country code, e.g. `en-US`")
            )
            return
        standardized_locale_name = f"{locale.language}-{locale.territory}"
        i18n.set_locale(standardized_locale_name)
        await self.bot._i18n_cache.set_locale(None, standardized_locale_name)
        await i18n.set_contextual_locales_from_guild(self.bot, ctx.guild)
        await ctx.send(_("Global locale has been set."))
        
    async def _local(self, ctx: commands.Context, language_code: str):
        if language_code.lower() == "default":
            global_locale = await self.bot._config.locale()
            i18n.set_contextual_locale(global_locale)
            await self.bot._i18n_cache.set_locale(ctx.guild, None)
            await ctx.send(_("Locale has been set to the default."))
            return
        try:
            locale = BabelLocale.parse(language_code, sep="-")
        except (ValueError, UnknownLocaleError):
            await ctx.send(_("Invalid language code. Use format: `en-US`"))
            return
        if locale.territory is None:
            await ctx.send(
                _("Invalid format - language code has to include country code, e.g. `en-US`")
            )
            return
        standardized_locale_name = f"{locale.language}-{locale.territory}"
        i18n.set_contextual_locale(standardized_locale_name)
        await self.bot._i18n_cache.set_locale(ctx.guild, standardized_locale_name)
        await ctx.send(_("Locale has been set."))