import io
import discord
import markdown
import random
import asyncio
import itertools
from string import ascii_letters, digits
from ..commands import CommandConverter, CogConverter
from redbot.core.commands import GuildConverter, RawUserIdConverter

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

import ISet

class bankset(ISet):
    def __init__(self):
        pass
    
    async def showsettings(self, ctx: commands.Context):
        """Show the current bank settings."""
        cur_setting = await bank.is_global()
        if cur_setting:
            group = bank._config
        else:
            if not ctx.guild:
                return
            group = bank._config.guild(ctx.guild)
        group_data = await group.all()
        bank_name = group_data["bank_name"]
        bank_scope = _("Global") if cur_setting else _("Server")
        currency_name = group_data["currency"]
        default_balance = group_data["default_balance"]
        max_balance = group_data["max_balance"]

        settings = _(
            "Bank settings:\n\nBank name: {bank_name}\nBank scope: {bank_scope}\n"
            "Currency: {currency_name}\nDefault balance: {default_balance}\n"
            "Maximum allowed balance: {maximum_bal}\n"
        ).format(
            bank_name=bank_name,
            bank_scope=bank_scope,
            currency_name=currency_name,
            default_balance=humanize_number(default_balance),
            maximum_bal=humanize_number(max_balance),
        )
        await ctx.send(box(settings))
    
    async def toggleglobal(self, ctx: commands.Context, confirm: bool = False):
        """Toggle whether the bank is global or not.

        If the bank is global, it will become per-server.
        If the bank is per-server, it will become global.
        """
        cur_setting = await bank.is_global()

        word = _("per-server") if cur_setting else _("global")
        if confirm is False:
            await ctx.send(
                _(
                    "This will toggle the bank to be {banktype}, deleting all accounts "
                    "in the process! If you're sure, type `{command}`"
                ).format(banktype=word, command=f"{ctx.clean_prefix}bankset toggleglobal yes")
            )
        else:
            await bank.set_global(not cur_setting)
            await ctx.send(_("The bank is now {banktype}.").format(banktype=word))
    
    async def bankname(self, ctx: commands.Context, *, name: str):
        """Set the bank's name."""
        await bank.set_bank_name(name, ctx.guild)
        await ctx.send(_("Bank name has been set to: {name}").format(name=name))
    
    async def creditsname(self, ctx:commands.Context, *, name: str):
        """Set the name for the bank's currency."""
        await bank.set_currency_name(name, ctx.guild)
        await ctx.send(_("Currency name has been set to: {name}").format(name=name))
    
    async def maxbal(self, ctx: commands.Context, *, amount: int):
        """Set the maximum balance a user can get."""
        try:
            await bank.set_max_balance(amount, ctx.guild)
        except ValueError:
            # noinspection PyProtectedMember
            return await ctx.send(
                _("Amount must be greater than zero and less than {max}.").format(
                    max=humanize_number(bank._MAX_BALANCE)
                )
            )
        await ctx.send(
            _("Maximum balance has been set to: {amount}").format(amount=humanize_number(amount))
        )
    
    async def registeramount(self, ctx: commands.Context, creds: int):
        """Set the initial balance for new bank accounts.

        Example:
            - `[p]bankset registeramount 5000`

        **Arguments**

        - `<creds>` The new initial balance amount. Default is 0.
        """
        guild = ctx.guild
        max_balance = await bank.get_max_balance(ctx.guild)
        credits_name = await bank.get_currency_name(guild)
        try:
            await bank.set_default_balance(creds, guild)
        except ValueError:
            return await ctx.send(
                _("Amount must be greater than or equal to zero and less than {maxbal}.").format(
                    maxbal=humanize_number(max_balance)
                )
            )
        await ctx.send(
            _("Registering an account will now give {num} {currency}.").format(
                num=humanize_number(creds), currency=credits_name
            )
        )
    
    async def reset(self, ctx: commands.Context, confirmation: bool = False):
        """Delete all bank accounts.

        Examples:
            - `[p]bankset reset` - Did not confirm. Shows the help message.
            - `[p]bankset reset yes`

        **Arguments**

        - `<confirmation>` This will default to false unless specified.
        """
        if confirmation is False:
            await ctx.send(
                _(
                    "This will delete all bank accounts for {scope}.\nIf you're sure, type "
                    "`{prefix}bankset reset yes`"
                ).format(
                    scope=self.bot.user.name if await bank.is_global() else _("this server"),
                    prefix=ctx.clean_prefix,
                )
            )
        else:
            await bank.wipe_bank(guild=ctx.guild)
            await ctx.send(
                _("All bank accounts for {scope} have been deleted.").format(
                    scope=self.bot.user.name if await bank.is_global() else _("this server")
                )
            )
    
    async def prune(self, ctx: commands.Context):
        """Base command for pruning bank accounts."""
        pass
    
    async def prune_local(self, ctx: commands.Context, confirmation: bool = False):
        """Prune bank accounts for users no longer in the server.

        Cannot be used with a global bank. See `[p]bankset prune global`.

        Examples:
            - `[p]bankset prune server` - Did not confirm. Shows the help message.
            - `[p]bankset prune server yes`

        **Arguments**

        - `<confirmation>` This will default to false unless specified.
        """
        global_bank = await bank.is_global()
        if global_bank is True:
            return await ctx.send(_("This command cannot be used with a global bank."))

        if confirmation is False:
            await ctx.send(
                _(
                    "This will delete all bank accounts for users no longer in this server."
                    "\nIf you're sure, type "
                    "`{prefix}bankset prune local yes`"
                ).format(prefix=ctx.clean_prefix)
            )
        else:
            await bank.bank_prune(self.bot, guild=ctx.guild)
            await ctx.send(
                _("Bank accounts for users no longer in this server have been deleted.")
            )
    
    async def prune_global(self, ctx: commands.Context, confirmation: bool = False):
        """Prune bank accounts for users no longer in the server.

        Cannot be used with a global bank. See `[p]bankset prune global`.

        Examples:
            - `[p]bankset prune server` - Did not confirm. Shows the help message.
            - `[p]bankset prune server yes`

        **Arguments**

        - `<confirmation>` This will default to false unless specified.
        """
        global_bank = await bank.is_global()
        if global_bank is True:
            return await ctx.send(_("This command cannot be used with a global bank."))

        if confirmation is False:
            await ctx.send(
                _(
                    "This will delete all bank accounts for users no longer in this server."
                    "\nIf you're sure, type "
                    "`{prefix}bankset prune local yes`"
                ).format(prefix=ctx.clean_prefix)
            )
        else:
            await bank.bank_prune(self.bot, guild=ctx.guild)
            await ctx.send(
                _("Bank accounts for users no longer in this server have been deleted.")
            )
    
    async def prune_user(self, ctx: commands.Context, member_or_id: Union[discord.Member, RawUserIdConverter], confirmation: bool = False,):
        """Delete the bank account of a specified user.

        Examples:
            - `[p]bankset prune user @Twentysix` - Did not confirm. Shows the help message.
            - `[p]bankset prune user @Twentysix yes`

        **Arguments**

        - `<user>` The user to delete the bank of. Takes mentions, names, and user ids.
        - `<confirmation>` This will default to false unless specified.
        """
        try:
            name = member_or_id.display_name
            uid = member_or_id.id
        except AttributeError:
            name = member_or_id
            uid = member_or_id

        if confirmation is False:
            await ctx.send(
                _(
                    "This will delete {name}'s bank account."
                    "\nIf you're sure, type "
                    "`{prefix}bankset prune user {id} yes`"
                ).format(prefix=ctx.clean_prefix, id=uid, name=name)
            )
        else:
            await bank.bank_prune(self.bot, guild=ctx.guild, user_id=uid)
            await ctx.send(_("The bank account for {name} has been pruned.").format(name=name))