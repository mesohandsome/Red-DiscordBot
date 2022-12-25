import io
import discord
import markdown
import random
import asyncio
import itertools
from string import ascii_letters, digits
from ...commands import CommandConverter, CogConverter

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

def entity_transformer(statement: str) -> str:
    return "".join(_entities.get(c, c) for c in statement)

import ISet

class helpset(ISet):
    def __init__(self, ctx: commands.Context):
        pass
    
    async def showsettings(self, ctx: commands.Context):
        """
        Show the current help settings.

        Warning: These settings may not be accurate if the default formatter is not in use.

        **Example:**
            - `[p]helpset showsettings`
        """

        help_settings = await commands.help.HelpSettings.from_context(ctx)

        if type(ctx.bot._help_formatter) is commands.help.RedHelpFormatter:
            message = help_settings.pretty
        else:
            message = _(
                "Warning: The default formatter is not in use, these settings may not apply."
            )
            message += f"\n\n{help_settings.pretty}"

        for page in pagify(message):
            await ctx.send(page)
    
    async def resetformatter(self, ctx: commands.Context):
        """
        This resets [botname]'s help formatter to the default formatter.

        **Example:**
            - `[p]helpset resetformatter`
        """

        ctx.bot.reset_help_formatter()
        await ctx.send(
            _(
                "The help formatter has been reset. "
                "This will not prevent cogs from modifying help, "
                "you may need to remove a cog if this has been an issue."
            )
        )
    
    async def resetsettings(self, ctx: commands.Context):
        """
        This resets [botname]'s help settings to their defaults.

        This may not have an impact when using custom formatters from 3rd party cogs

        **Example:**
            - `[p]helpset resetsettings`
        """
        await ctx.bot._config.help.clear()
        await ctx.send(
            _(
                "The help settings have been reset to their defaults. "
                "This may not have an impact when using 3rd party help formatters."
            )
        )
    
    async def usemenus(self, ctx: commands.Context, use_menus: Literal["buttons", "reactions", "select", "selectonly", "disable"],):
        """
        Allows the help command to be sent as a paginated menu instead of separate
        messages.

        When "reactions", "buttons", "select", or "selectonly" is passed,
         `[p]help` will only show one page at a time
        and will use the associated control scheme to navigate between pages.

         **Examples:**
            - `[p]helpset usemenus reactions` - Enables using reaction menus.
            - `[p]helpset usemenus buttons` - Enables using button menus.
            - `[p]helpset usemenus select` - Enables buttons with a select menu.
            - `[p]helpset usemenus selectonly` - Enables a select menu only on help.
            - `[p]helpset usemenus disable` - Disables help menus.

        **Arguments:**
            - `<"buttons"|"reactions"|"select"|"selectonly"|"disable">` - Whether to use `buttons`,
            `reactions`, `select`, `selectonly`, or no menus.
        """
        if use_menus == "selectonly":
            msg = _("Help will use the select menu only.")
            await ctx.bot._config.help.use_menus.set(4)
        if use_menus == "select":
            msg = _("Help will use button menus and add a select menu.")
            await ctx.bot._config.help.use_menus.set(3)
        if use_menus == "buttons":
            msg = _("Help will use button menus.")
            await ctx.bot._config.help.use_menus.set(2)
        if use_menus == "reactions":
            msg = _("Help will use reaction menus.")
            await ctx.bot._config.help.use_menus.set(1)
        if use_menus == "disabled":
            msg = _("Help will not use menus.")
            await ctx.bot._config.help.use_menus.set(0)

        await ctx.send(msg)
    
    async def showhidden(self, ctx: commands.Context, show_hidden: bool = None):
        """
        This allows the help command to show hidden commands.

        This defaults to False.
        Using this without a setting will toggle.

        **Examples:**
            - `[p]helpset showhidden True` - Enables showing hidden commands.
            - `[p]helpset showhidden` - Toggles the value.

        **Arguments:**
            - `[show_hidden]` - Whether to use show hidden commands in help. Leave blank to toggle.
        """
        if show_hidden is None:
            show_hidden = not await ctx.bot._config.help.show_hidden()
        await ctx.bot._config.help.show_hidden.set(show_hidden)
        if show_hidden:
            await ctx.send(_("Help will not filter hidden commands."))
        else:
            await ctx.send(_("Help will filter hidden commands."))
    
    async def showaliases(self, ctx: commands.Context, show_aliases: bool = None):
        """
        This allows the help command to show existing commands aliases if there is any.

        This defaults to True.
        Using this without a setting will toggle.

        **Examples:**
            - `[p]helpset showaliases False` - Disables showing aliases on this server.
            - `[p]helpset showaliases` - Toggles the value.

        **Arguments:**
            - `[show_aliases]` - Whether to include aliases in help. Leave blank to toggle.
        """
        if show_aliases is None:
            show_aliases = not await ctx.bot._config.help.show_aliases()
        await ctx.bot._config.help.show_aliases.set(show_aliases)
        if show_aliases:
            await ctx.send(_("Help will now show command aliases."))
        else:
            await ctx.send(_("Help will no longer show command aliases."))
    
    async def usetick(self, ctx: commands.Context, use_tick: bool = None):
        """
        This allows the help command message to be ticked if help is sent to a DM.

        Ticking is reacting to the help message with a ✅.

        Defaults to False.
        Using this without a setting will toggle.

        Note: This is only used when the bot is not using menus.

        **Examples:**
            - `[p]helpset usetick False` - Disables ticking when help is sent to DMs.
            - `[p]helpset usetick` - Toggles the value.

        **Arguments:**
            - `[use_tick]` - Whether to tick the help command when help is sent to DMs. Leave blank to toggle.
        """
        if use_tick is None:
            use_tick = not await ctx.bot._config.help.use_tick()
        await ctx.bot._config.help.use_tick.set(use_tick)
        if use_tick:
            await ctx.send(_("Help will now tick the command when sent in a DM."))
        else:
            await ctx.send(_("Help will not tick the command when sent in a DM."))
    
    async def permfilter(self, ctx: commands.Context, verify: bool = None):
        """
        Sets if commands which can't be run in the current context should be filtered from help.

        Defaults to True.
        Using this without a setting will toggle.

        **Examples:**
            - `[p]helpset verifychecks False` - Enables showing unusable commands in help.
            - `[p]helpset verifychecks` - Toggles the value.

        **Arguments:**
            - `[verify]` - Whether to hide unusable commands in help. Leave blank to toggle.
        """
        if verify is None:
            verify = not await ctx.bot._config.help.verify_checks()
        await ctx.bot._config.help.verify_checks.set(verify)
        if verify:
            await ctx.send(_("Help will only show for commands which can be run."))
        else:
            await ctx.send(_("Help will show up without checking if the commands can be run."))
    
    async def verifyexists(self, ctx: commands.Context, verify: bool = None):
        """
        Sets whether the bot should respond to help commands for nonexistent topics.

        When enabled, this will indicate the existence of help topics, even if the user can't use it.

        Note: This setting on its own does not fully prevent command enumeration.

        Defaults to False.
        Using this without a setting will toggle.

        **Examples:**
            - `[p]helpset verifyexists True` - Enables sending help for nonexistent topics.
            - `[p]helpset verifyexists` - Toggles the value.

        **Arguments:**
            - `[verify]` - Whether to respond to help for nonexistent topics. Leave blank to toggle.
        """
        if verify is None:
            verify = not await ctx.bot._config.help.verify_exists()
        await ctx.bot._config.help.verify_exists.set(verify)
        if verify:
            await ctx.send(_("Help will verify the existence of help topics."))
        else:
            await ctx.send(
                _(
                    "Help will only verify the existence of "
                    "help topics via fuzzy help (if enabled)."
                )
            )
    
    async def pagecharlimt(self, ctx: commands.Context, limit: int):
        """Set the character limit for each page in the help message.

        Note: This setting only applies to embedded help.

        The default value is 1000 characters. The minimum value is 500.
        The maximum is based on the lower of what you provide and what discord allows.

        Please note that setting a relatively small character limit may
        mean some pages will exceed this limit.

        **Example:**
            - `[p]helpset pagecharlimit 1500`

        **Arguments:**
            - `<limit>` - The max amount of characters to show per page in the help message.
        """
        if limit < 500:
            await ctx.send(_("You must give a value of at least 500 characters."))
            return

        await ctx.bot._config.help.page_char_limit.set(limit)
        await ctx.send(_("Done. The character limit per page has been set to {}.").format(limit))
    
    async def maxpages(self, ctx: commands.Context, pages: int):
        """Set the maximum number of help pages sent in a server channel.

        Note: This setting does not apply to menu help.

        If a help message contains more pages than this value, the help message will
        be sent to the command author via DM. This is to help reduce spam in server
        text channels.

        The default value is 2 pages.

        **Examples:**
            - `[p]helpset maxpages 50` - Basically never send help to DMs.
            - `[p]helpset maxpages 0` - Always send help to DMs.

        **Arguments:**
            - `<limit>` - The max pages allowed to send per help in a server.
        """
        if pages < 0:
            await ctx.send(_("You must give a value of zero or greater!"))
            return

        await ctx.bot._config.help.max_pages_in_guild.set(pages)
        await ctx.send(_("Done. The page limit has been set to {}.").format(pages))
    
    async def deletedelay(self, ctx: commands.Context, seconds: int):
        """Set the delay after which help pages will be deleted.

        The setting is disabled by default, and only applies to non-menu help,
        sent in server text channels.
        Setting the delay to 0 disables this feature.

        The bot has to have MANAGE_MESSAGES permission for this to work.

        **Examples:**
            - `[p]helpset deletedelay 60` - Delete the help pages after a minute.
            - `[p]helpset deletedelay 1` - Delete the help pages as quickly as possible.
            - `[p]helpset deletedelay 1209600` - Max time to wait before deleting (14 days).
            - `[p]helpset deletedelay 0` - Disable deleting help pages.

        **Arguments:**
            - `<seconds>` - The seconds to wait before deleting help pages.
        """
        if seconds < 0:
            await ctx.send(_("You must give a value of zero or greater!"))
            return
        if seconds > 60 * 60 * 24 * 14:  # 14 days
            await ctx.send(_("The delay cannot be longer than 14 days!"))
            return

        await ctx.bot._config.help.delete_delay.set(seconds)
        if seconds == 0:
            await ctx.send(_("Done. Help messages will not be deleted now."))
        else:
            await ctx.send(_("Done. The delete delay has been set to {} seconds.").format(seconds))
    
    async def reacttimeout(self, ctx: commands.Context, seconds: int):
        """Set the timeout for reactions, if menus are enabled.

        The default is 30 seconds.
        The timeout has to be between 15 and 300 seconds.

        **Examples:**
            - `[p]helpset reacttimeout 30` - The default timeout.
            - `[p]helpset reacttimeout 60` - Timeout of 1 minute.
            - `[p]helpset reacttimeout 15` - Minimum allowed timeout.
            - `[p]helpset reacttimeout 300` - Max allowed timeout (5 mins).

        **Arguments:**
            - `<seconds>` - The timeout, in seconds, of the reactions.
        """
        if seconds < 15:
            await ctx.send(_("You must give a value of at least 15 seconds!"))
            return
        if seconds > 300:
            await ctx.send(_("The timeout cannot be greater than 5 minutes!"))
            return

        await ctx.bot._config.help.react_timeout.set(seconds)
        await ctx.send(_("Done. The reaction timeout has been set to {} seconds.").format(seconds))
    
    async def tagline(self, ctx: commands.Context, *, tagline: str = None):
        """
        Set the tagline to be used.

        The maximum tagline length is 2048 characters.
        This setting only applies to embedded help. If no tagline is specified, the default will be used instead.

        **Examples:**
            - `[p]helpset tagline Thanks for using the bot!`
            - `[p]helpset tagline` - Resets the tagline to the default.

        **Arguments:**
            - `[tagline]` - The tagline to appear at the bottom of help embeds. Leave blank to reset.
        """
        if tagline is None:
            await ctx.bot._config.help.tagline.set("")
            return await ctx.send(_("The tagline has been reset."))

        if len(tagline) > 2048:
            await ctx.send(
                _(
                    "Your tagline is too long! Please shorten it to be "
                    "no more than 2048 characters long."
                )
            )
            return

        await ctx.bot._config.help.tagline.set(tagline)
        await ctx.send(_("The tagline has been set."))