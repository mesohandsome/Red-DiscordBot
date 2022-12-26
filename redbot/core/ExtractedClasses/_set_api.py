import io
import discord
import markdown
import random
import asyncio
from string import ascii_letters, digits
from redbot.core.utils.views import SetApiView


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


class _set_api:
    async def __init__(self, ctx: commands.Context, service: Optional[str] = None, *, tokens: Optional[TokenConverter] = None):
        if service is None:  # Handled in order of missing operations
            await ctx.send(_("Click the button below to set your keys."), view=SetApiView())
        elif tokens is None:
            await ctx.send(
                _("Click the button below to set your keys."),
                view=SetApiView(default_service=service),
            )
        else:
            if ctx.bot_permissions.manage_messages:
                await ctx.message.delete()
            await ctx.bot.set_shared_api_tokens(service, **tokens)
            await ctx.send(_("`{service}` API tokens have been set.").format(service=service))
    
    async def _list(self, ctx: commands.Context):
        services: dict = await ctx.bot.get_shared_api_tokens()
        if not services:
            await ctx.send(_("No API services have been set yet."))
            return

        sorted_services = sorted(services.keys(), key=str.lower)

        joined = _("Set API services:\n") if len(services) > 1 else _("Set API service:\n")
        for service_name in sorted_services:
            joined += "+ {}\n".format(service_name)
            for key_name in services[service_name].keys():
                joined += "  - {}\n".format(key_name)
        for page in pagify(joined, ["\n"], shorten_by=16):
            await ctx.send(box(page.lstrip(" "), lang="diff"))
    
    async def _remove(self, ctx: commands.Context, *services: str):
        bot_services = (await ctx.bot.get_shared_api_tokens()).keys()
        services = [s for s in services if s in bot_services]

        if services:
            await self.bot.remove_shared_api_services(*services)
            if len(services) > 1:
                msg = _("Services deleted successfully:\n{services_list}").format(
                    services_list=humanize_list(services)
                )
            else:
                msg = _("Service deleted successfully: {service_name}").format(
                    service_name=services[0]
                )
            await ctx.send(msg)
        else:
            await ctx.send(_("None of the services you provided had any keys set."))