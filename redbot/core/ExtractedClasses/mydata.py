import io
import discord
import markdown
import random
import asyncio
from string import ascii_letters, digits

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

HTML_CLOSING = "</body></html>"
PRETTY_HTML_HEAD = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>3rd Party Data Statements</title>
<style type="text/css">
body{margin:2em auto;max-width:800px;line-height:1.4;font-size:16px;
background-color=#EEEEEE;color:#454545;padding:1em;text-align:justify}
h1,h2,h3{line-height:1.2}
</style></head><body>
"""  # This ends up being a small bit extra that really makes a difference.

class mydata:
    def __init__(self):
        pass
    
    async def whatdata(self, ctx: commands.Context):
        ver = "latest" if red_version_info.dev_release else "stable"
        link = f"https://docs.discord.red/en/{ver}/red_core_data_statement.html"
        await ctx.send(
            _(
                "This bot stores some data about users as necessary to function. "
                "This is mostly the ID your user is assigned by Discord, linked to "
                "a handful of things depending on what you interact with in the bot. "
                "There are a few commands which store it to keep track of who created "
                "something. (such as playlists) "
                "For full details about this as well as more in depth details of what "
                "is stored and why, see {link}.\n\n"
                "Additionally, 3rd party addons loaded by the bot's owner may or "
                "may not store additional things. "
                "You can use `{prefix}mydata 3rdparty` "
                "to view the statements provided by each 3rd-party addition."
            ).format(link=link, prefix=ctx.clean_prefix)
        )
    
    async def third_party(self, ctx: commands.Context):
        """View the End User Data statements of each 3rd-party module.

        This will send an attachment with the End User Data statements of all loaded 3rd party cogs.

        **Example:**
            - `[p]mydata 3rdparty`
        """

        # Can't check this as a command check, and want to prompt DMs as an option.
        if not ctx.bot_permissions.attach_files:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(_("I need to be able to attach files (try in DMs?)."))

        statements = {
            ext_name: getattr(ext, "__red_end_user_data_statement__", None)
            for ext_name, ext in ctx.bot.extensions.items()
            if not (ext.__package__ and ext.__package__.startswith("redbot."))
        }

        if not statements:
            return await ctx.send(
                _("This instance does not appear to have any 3rd-party extensions loaded.")
            )

        parts = []

        formatted_statements = []

        no_statements = []

        for ext_name, statement in sorted(statements.items()):
            if not statement:
                no_statements.append(ext_name)
            else:
                formatted_statements.append(
                    f"### {entity_transformer(ext_name)}\n\n{entity_transformer(statement)}"
                )

        if formatted_statements:
            parts.append(
                "## "
                + _("3rd party End User Data statements")
                + "\n\n"
                + _("The following are statements provided by 3rd-party extensions.")
            )
            parts.extend(formatted_statements)

        if no_statements:
            parts.append("## " + _("3rd-party extensions without statements\n"))
            for ext in no_statements:
                parts.append(f"\n - {entity_transformer(ext)}")

        generated = markdown.markdown("\n".join(parts), output_format="html")

        html = "\n".join((PRETTY_HTML_HEAD, generated, HTML_CLOSING))

        fp = io.BytesIO(html.encode())

        await ctx.send(
            _("Here's a generated page with the statements provided by 3rd-party extensions."),
            file=discord.File(fp, filename="3rd-party.html"),
        )
    
    async def get_serious_confirmation(self, ctx: commands.Context, prompt: str) -> bool:
        confirm_token = "".join(random.choices((*ascii_letters, *digits), k=8))

        await ctx.send(f"{prompt}\n\n{confirm_token}")
        try:
            message = await ctx.bot.wait_for(
                "message",
                check=lambda m: m.channel.id == ctx.channel.id and m.author.id == ctx.author.id,
                timeout=30,
            )
        except asyncio.TimeoutError:
            await ctx.send(_("Did not get confirmation, cancelling."))
        else:
            if message.content.strip() == confirm_token:
                return True
            else:
                await ctx.send(_("Did not get a matching confirmation, cancelling."))

        return False
    
    async def forgetme(self, ctx: commands.Context):
        """
        Have [botname] forget what it knows about you.

        This may not remove all data about you, data needed for operation,
        such as command cooldowns will be kept until no longer necessary.

        Further interactions with [botname] may cause it to learn about you again.

        **Example:**
            - `[p]mydata forgetme`
        """
        if ctx.assume_yes:
            # lol, no, we're not letting users schedule deletions every day to thrash the bot.
            ctx.command.reset_cooldown(ctx)  # We will however not let that lock them out either.
            return await ctx.send(
                _("This command ({command}) does not support non-interactive usage.").format(
                    command=ctx.command.qualified_name
                )
            )

        if not await self.get_serious_confirmation(
            ctx,
            _(
                "This will cause the bot to get rid of and/or disassociate "
                "data from you. It will not get rid of operational data such "
                "as modlog entries, warnings, or mutes. "
                "If you are sure this is what you want, "
                "please respond with the following:"
            ),
        ):
            ctx.command.reset_cooldown(ctx)
            return
        await ctx.send(_("This may take some time."))

        if await ctx.bot._config.datarequests.user_requests_are_strict():
            requester = "user_strict"
        else:
            requester = "user"

        results = await self.bot.handle_data_deletion_request(
            requester=requester, user_id=ctx.author.id
        )

        if results.failed_cogs and results.failed_modules:
            await ctx.send(
                _(
                    "I tried to delete all non-operational data about you "
                    "(that I know how to delete) "
                    "{mention}, however the following modules errored: {modules}. "
                    "Additionally, the following cogs errored: {cogs}.\n"
                    "Please contact the owner of this bot to address this.\n"
                    "Note: Outside of these failures, data should have been deleted."
                ).format(
                    mention=ctx.author.mention,
                    cogs=humanize_list(results.failed_cogs),
                    modules=humanize_list(results.failed_modules),
                )
            )
        elif results.failed_cogs:
            await ctx.send(
                _(
                    "I tried to delete all non-operational data about you "
                    "(that I know how to delete) "
                    "{mention}, however the following cogs errored: {cogs}.\n"
                    "Please contact the owner of this bot to address this.\n"
                    "Note: Outside of these failures, data should have been deleted."
                ).format(mention=ctx.author.mention, cogs=humanize_list(results.failed_cogs))
            )
        elif results.failed_modules:
            await ctx.send(
                _(
                    "I tried to delete all non-operational data about you "
                    "(that I know how to delete) "
                    "{mention}, however the following modules errored: {modules}.\n"
                    "Please contact the owner of this bot to address this.\n"
                    "Note: Outside of these failures, data should have been deleted."
                ).format(mention=ctx.author.mention, modules=humanize_list(results.failed_modules))
            )
        else:
            await ctx.send(
                _(
                    "I've deleted any non-operational data about you "
                    "(that I know how to delete) {mention}"
                ).format(mention=ctx.author.mention)
            )

        if results.unhandled:
            await ctx.send(
                _("{mention} The following cogs did not handle deletion:\n{cogs}.").format(
                    mention=ctx.author.mention, cogs=humanize_list(results.unhandled)
                )
            )

    async def getdata(self, ctx: commands.Context):
        """[Coming Soon] Get what data [botname] has about you."""
        await ctx.send(
            _(
                "This command doesn't do anything yet, "
                "but we're working on adding support for this."
            )
        )
    
    async def owner_management(self, ctx: commands.Context):
        """
        Commands for more complete data handling.
        """
    
    async def owner_allow_user_deletions(self, ctx: commands.Context):
        """
        Set the bot to allow users to request a data deletion.

        This is on by default.
        Opposite of `[p]mydata ownermanagement disallowuserdeletions`

        **Example:**
            - `[p]mydata ownermanagement allowuserdeletions`
        """
        await ctx.bot._config.datarequests.allow_user_requests.set(True)
        await ctx.send(
            _(
                "User can delete their own data. "
                "This will not include operational data such as blocked users."
            )
        )
    
    async def owner_disallow_user_deletions(self, ctx: commands.Context):
        """
        Set the bot to not allow users to request a data deletion.

        Opposite of `[p]mydata ownermanagement allowuserdeletions`

        **Example:**
            - `[p]mydata ownermanagement disallowuserdeletions`
        """
        await ctx.bot._config.datarequests.allow_user_requests.set(False)
        await ctx.send(_("User can not delete their own data."))
    
    async def owner_user_deletion_level(self, ctx: commands.Context, level: int):
        """
        Sets how user deletions are treated.

        **Example:**
            - `[p]mydata ownermanagement setuserdeletionlevel 1`

        **Arguments:**
            - `<level>` - The strictness level for user deletion. See Level guide below.

        Level:
            - `0`: What users can delete is left entirely up to each cog.
            - `1`: Cogs should delete anything the cog doesn't need about the user.
        """

        if level == 1:
            await ctx.bot._config.datarequests.user_requests_are_strict.set(True)
            await ctx.send(
                _(
                    "Cogs will be instructed to remove all non operational "
                    "data upon a user request."
                )
            )
        elif level == 0:
            await ctx.bot._config.datarequests.user_requests_are_strict.set(False)
            await ctx.send(
                _(
                    "Cogs will be informed a user has made a data deletion request, "
                    "and the details of what to delete will be left to the "
                    "discretion of the cog author."
                )
            )
        else:
            await ctx.send_help()
    
    async def discord_deletion_request(self, ctx: commands.Context, user_id: int):
        """
        Handle a deletion request from Discord.

        This will cause the bot to get rid of or disassociate all data from the specified user ID.
        You should not use this unless Discord has specifically requested this with regard to a deleted user.
        This will remove the user from various anti-abuse measures.
        If you are processing a manual request from a user, you may want `[p]mydata ownermanagement deleteforuser` instead.

        **Arguments:**
            - `<user_id>` - The id of the user whose data would be deleted.
        """

        if not await self.get_serious_confirmation(
            ctx,
            _(
                "This will cause the bot to get rid of or disassociate all data "
                "from the specified user ID. You should not use this unless "
                "Discord has specifically requested this with regard to a deleted user. "
                "This will remove the user from various anti-abuse measures. "
                "If you are processing a manual request from a user, you may want "
                "`{prefix}{command_name}` instead."
                "\n\nIf you are sure this is what you intend to do "
                "please respond with the following:"
            ).format(prefix=ctx.clean_prefix, command_name="mydata ownermanagement deleteforuser"),
        ):
            return
        results = await self.bot.handle_data_deletion_request(
            requester="discord_deleted_user", user_id=user_id
        )

        if results.failed_cogs and results.failed_modules:
            await ctx.send(
                _(
                    "I tried to delete all data about that user, "
                    "(that I know how to delete) "
                    "however the following modules errored: {modules}. "
                    "Additionally, the following cogs errored: {cogs}\n"
                    "Please check your logs and contact the creators of "
                    "these cogs and modules.\n"
                    "Note: Outside of these failures, data should have been deleted."
                ).format(
                    cogs=humanize_list(results.failed_cogs),
                    modules=humanize_list(results.failed_modules),
                )
            )
        elif results.failed_cogs:
            await ctx.send(
                _(
                    "I tried to delete all data about that user, "
                    "(that I know how to delete) "
                    "however the following cogs errored: {cogs}.\n"
                    "Please check your logs and contact the creators of "
                    "these cogs and modules.\n"
                    "Note: Outside of these failures, data should have been deleted."
                ).format(cogs=humanize_list(results.failed_cogs))
            )
        elif results.failed_modules:
            await ctx.send(
                _(
                    "I tried to delete all data about that user, "
                    "(that I know how to delete) "
                    "however the following modules errored: {modules}.\n"
                    "Please check your logs and contact the creators of "
                    "these cogs and modules.\n"
                    "Note: Outside of these failures, data should have been deleted."
                ).format(modules=humanize_list(results.failed_modules))
            )
        else:
            await ctx.send(_("I've deleted all data about that user that I know how to delete."))

        if results.unhandled:
            await ctx.send(
                _("{mention} The following cogs did not handle deletion:\n{cogs}.").format(
                    mention=ctx.author.mention, cogs=humanize_list(results.unhandled)
                )
            )
    
    async def user_deletion_request_by_owner(self, ctx: commands.Context, user_id: int):
        """Delete data [botname] has about a user for a user.

        This will cause the bot to get rid of or disassociate a lot of non-operational data from the specified user.
        Users have access to a different command for this unless they can't interact with the bot at all.
        This is a mostly safe operation, but you should not use it unless processing a request from this user as it may impact their usage of the bot.

        **Arguments:**
            - `<user_id>` - The id of the user whose data would be deleted.
        """
        if not await self.get_serious_confirmation(
            ctx,
            _(
                "This will cause the bot to get rid of or disassociate "
                "a lot of non-operational data from the "
                "specified user. Users have access to "
                "different command for this unless they can't interact with the bot at all. "
                "This is a mostly safe operation, but you should not use it "
                "unless processing a request from this "
                "user as it may impact their usage of the bot. "
                "\n\nIf you are sure this is what you intend to do "
                "please respond with the following:"
            ),
        ):
            return

        if await ctx.bot._config.datarequests.user_requests_are_strict():
            requester = "user_strict"
        else:
            requester = "user"

        results = await self.bot.handle_data_deletion_request(requester=requester, user_id=user_id)

        if results.failed_cogs and results.failed_modules:
            await ctx.send(
                _(
                    "I tried to delete all non-operational data about that user, "
                    "(that I know how to delete) "
                    "however the following modules errored: {modules}. "
                    "Additionally, the following cogs errored: {cogs}\n"
                    "Please check your logs and contact the creators of "
                    "these cogs and modules.\n"
                    "Note: Outside of these failures, data should have been deleted."
                ).format(
                    cogs=humanize_list(results.failed_cogs),
                    modules=humanize_list(results.failed_modules),
                )
            )
        elif results.failed_cogs:
            await ctx.send(
                _(
                    "I tried to delete all non-operational data about that user, "
                    "(that I know how to delete) "
                    "however the following cogs errored: {cogs}.\n"
                    "Please check your logs and contact the creators of "
                    "these cogs and modules.\n"
                    "Note: Outside of these failures, data should have been deleted."
                ).format(cogs=humanize_list(results.failed_cogs))
            )
        elif results.failed_modules:
            await ctx.send(
                _(
                    "I tried to delete all non-operational data about that user, "
                    "(that I know how to delete) "
                    "however the following modules errored: {modules}.\n"
                    "Please check your logs and contact the creators of "
                    "these cogs and modules.\n"
                    "Note: Outside of these failures, data should have been deleted."
                ).format(modules=humanize_list(results.failed_modules))
            )
        else:
            await ctx.send(
                _(
                    "I've deleted all non-operational data about that user "
                    "that I know how to delete."
                )
            )

        if results.unhandled:
            await ctx.send(
                _("{mention} The following cogs did not handle deletion:\n{cogs}.").format(
                    mention=ctx.author.mention, cogs=humanize_list(results.unhandled)
                )
            )
    
    async def user_deletion_by_owner(self, ctx: commands.Context, user_id: int):
        """Delete data [botname] has about a user.

        This will cause the bot to get rid of or disassociate a lot of data about the specified user.
        This may include more than just end user data, including anti abuse records.

        **Arguments:**
            - `<user_id>` - The id of the user whose data would be deleted.
        """
        if not await self.get_serious_confirmation(
            ctx,
            _(
                "This will cause the bot to get rid of or disassociate "
                "a lot of data about the specified user. "
                "This may include more than just end user data, including "
                "anti abuse records."
                "\n\nIf you are sure this is what you intend to do "
                "please respond with the following:"
            ),
        ):
            return
        results = await self.bot.handle_data_deletion_request(requester="owner", user_id=user_id)

        if results.failed_cogs and results.failed_modules:
            await ctx.send(
                _(
                    "I tried to delete all data about that user, "
                    "(that I know how to delete) "
                    "however the following modules errored: {modules}. "
                    "Additionally, the following cogs errored: {cogs}\n"
                    "Please check your logs and contact the creators of "
                    "these cogs and modules.\n"
                    "Note: Outside of these failures, data should have been deleted."
                ).format(
                    cogs=humanize_list(results.failed_cogs),
                    modules=humanize_list(results.failed_modules),
                )
            )
        elif results.failed_cogs:
            await ctx.send(
                _(
                    "I tried to delete all data about that user, "
                    "(that I know how to delete) "
                    "however the following cogs errored: {cogs}.\n"
                    "Please check your logs and contact the creators of "
                    "these cogs and modules.\n"
                    "Note: Outside of these failures, data should have been deleted."
                ).format(cogs=humanize_list(results.failed_cogs))
            )
        elif results.failed_modules:
            await ctx.send(
                _(
                    "I tried to delete all data about that user, "
                    "(that I know how to delete) "
                    "however the following modules errored: {modules}.\n"
                    "Please check your logs and contact the creators of "
                    "these cogs and modules.\n"
                    "Note: Outside of these failures, data should have been deleted."
                ).format(modules=humanize_list(results.failed_modules))
            )
        else:
            await ctx.send(_("I've deleted all data about that user that I know how to delete."))

        if results.unhandled:
            await ctx.send(
                _("{mention} The following cogs did not handle deletion:\n{cogs}.").format(
                    mention=ctx.author.mention, cogs=humanize_list(results.unhandled)
                )
            )