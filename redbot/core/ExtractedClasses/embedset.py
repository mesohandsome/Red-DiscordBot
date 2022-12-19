import io
import discord
import markdown
import random
import asyncio
import itertools
from string import ascii_letters, digits
from ..commands import CommandConverter, CogConverter

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

class embedset:
    def __init__(self):
        pass
    
    async def showsettings(self, ctx: commands.Context, command: CommandConverter = None) -> None:
        """
        Show the current embed settings.

        Provide a command name to check for command specific embed settings.

        **Examples:**
            - `[p]embedset showsettings` - Shows embed settings.
            - `[p]embedset showsettings info` - Also shows embed settings for the 'info' command.
            - `[p]embedset showsettings "ignore list"` - Checking subcommands requires quotes.

        **Arguments:**
            - `[command]` - Checks this command for command specific embed settings.
        """
        # qualified name might be different if alias was passed to this command
        command_name = command and command.qualified_name

        text = _("Embed settings:\n\n")
        global_default = await self.bot._config.embeds()
        text += _("Global default: {value}\n").format(value=global_default)

        if command_name is not None:
            scope = self.bot._config.custom("COMMAND", command_name, 0)
            global_command_setting = await scope.embeds()
            text += _("Global command setting for {command} command: {value}\n").format(
                command=inline(command_name), value=global_command_setting
            )

        if ctx.guild:
            guild_setting = await self.bot._config.guild(ctx.guild).embeds()
            text += _("Guild setting: {value}\n").format(value=guild_setting)

            if command_name is not None:
                scope = self.bot._config.custom("COMMAND", command_name, ctx.guild.id)
                command_setting = await scope.embeds()
                text += _("Server command setting for {command} command: {value}\n").format(
                    command=inline(command_name), value=command_setting
                )

        if ctx.channel:
            channel_setting = await self.bot._config.channel(ctx.channel).embeds()
            text += _("Channel setting: {value}\n").format(value=channel_setting)

        user_setting = await self.bot._config.user(ctx.author).embeds()
        text += _("User setting: {value}").format(value=user_setting)
        await ctx.send(box(text))
    
    async def guild(self, ctx: commands.Context, enabled: bool) -> None:
        """
        Set the server's embed setting.

        If set, this is used instead of the global default to determine whether or not to use embeds.
        This is used for all commands done in a server.

        If enabled is left blank, the setting will be unset and the global default will be used instead.

        To see full evaluation order of embed settings, run `[p]help embedset`.

        **Examples:**
            - `[p]embedset server False` - Disables embeds on this server.
            - `[p]embedset server` - Resets value to use global default.

        **Arguments:**
            - `[enabled]` - Whether to use embeds on this server. Leave blank to reset to default.
        """
        if enabled is None:
            await self.bot._config.guild(ctx.guild).embeds.clear()
            await ctx.send(_("Embeds will now fall back to the global setting."))
            return

        await self.bot._config.guild(ctx.guild).embeds.set(enabled)
        await ctx.send(
            _("Embeds are now enabled for this guild.")
            if enabled
            else _("Embeds are now disabled for this guild.")
        )
    
    async def command_guild(self, ctx: commands.GuildContext, command: CommandConverter, enabled: bool = None):
        """
        Sets a commmand's embed setting for the current server.

        If set, this is used instead of the server default to determine whether or not to use embeds.

        If enabled is left blank, the setting will be unset and the server default will be used instead.

        To see full evaluation order of embed settings, run `[p]help embedset`.

        **Examples:**
            - `[p]embedset command server info` - Clears command specific embed settings for 'info'.
            - `[p]embedset command server info False` - Disables embeds for 'info'.
            - `[p]embedset command server "ignore list" True` - Quotes are needed for subcommands.

        **Arguments:**
            - `[enabled]` - Whether to use embeds for this command. Leave blank to reset to default.
        """
        self._check_if_command_requires_embed_links(command)
        # qualified name might be different if alias was passed to this command
        command_name = command.qualified_name

        if enabled is None:
            await self.bot._config.custom("COMMAND", command_name, ctx.guild.id).embeds.clear()
            await ctx.send(_("Embeds will now fall back to the server setting."))
            return

        await self.bot._config.custom("COMMAND", command_name, ctx.guild.id).embeds.set(enabled)
        if enabled:
            await ctx.send(
                _("Embeds are now enabled for {command_name} command.").format(
                    command_name=inline(command_name)
                )
            )
        else:
            await ctx.send(
                _("Embeds are now disabled for {command_name} command.").format(
                    command_name=inline(command_name)
                )
            )
    
    async def command_global(self, ctx: commands.Context, command: CommandConverter, enabled: bool = None):
        """
        Sets a command's embed setting globally.

        If set, this is used instead of the global default to determine whether or not to use embeds.

        If enabled is left blank, the setting will be unset.

        To see full evaluation order of embed settings, run `[p]help embedset`.

        **Examples:**
            - `[p]embedset command global info` - Clears command specific embed settings for 'info'.
            - `[p]embedset command global info False` - Disables embeds for 'info'.
            - `[p]embedset command global "ignore list" True` - Quotes are needed for subcommands.

        **Arguments:**
            - `[enabled]` - Whether to use embeds for this command. Leave blank to reset to default.
        """
        self._check_if_command_requires_embed_links(command)
        # qualified name might be different if alias was passed to this command
        command_name = command.qualified_name

        if enabled is None:
            await self.bot._config.custom("COMMAND", command_name, 0).embeds.clear()
            await ctx.send(_("Embeds will now fall back to the global setting."))
            return

        await self.bot._config.custom("COMMAND", command_name, 0).embeds.set(enabled)
        if enabled:
            await ctx.send(
                _("Embeds are now enabled for {command_name} command.").format(
                    command_name=inline(command_name)
                )
            )
        else:
            await ctx.send(
                _("Embeds are now disabled for {command_name} command.").format(
                    command_name=inline(command_name)
                )
            )
    
    async def channel(self, ctx: commands.Context, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.ForumChannel], enabled: bool = None,):
        """
        Set's a channel's embed setting.

        If set, this is used instead of the guild and command defaults to determine whether or not to use embeds.
        This is used for all commands done in a channel.

        If enabled is left blank, the setting will be unset and the guild default will be used instead.

        To see full evaluation order of embed settings, run `[p]help embedset`.

        **Examples:**
            - `[p]embedset channel #text-channel False` - Disables embeds in the #text-channel.
            - `[p]embedset channel #forum-channel disable` - Disables embeds in the #forum-channel.
            - `[p]embedset channel #text-channel` - Resets value to use guild default in the #text-channel .

        **Arguments:**
            - `<channel>` - The text, voice, or forum channel to set embed setting for.
            - `[enabled]` - Whether to use embeds in this channel. Leave blank to reset to default.
        """
        if enabled is None:
            await self.bot._config.channel(channel).embeds.clear()
            await ctx.send(_("Embeds will now fall back to the global setting."))
            return

        await self.bot._config.channel(channel).embeds.set(enabled)
        await ctx.send(
            _("Embeds are now {} for this channel.").format(
                _("enabled") if enabled else _("disabled")
            )
        )
    
    async def user(self, ctx:commands.Context, enabled: bool = None):
        """
        Sets personal embed setting for DMs.

        If set, this is used instead of the global default to determine whether or not to use embeds.
        This is used for all commands executed in a DM with the bot.

        If enabled is left blank, the setting will be unset and the global default will be used instead.

        To see full evaluation order of embed settings, run `[p]help embedset`.

        **Examples:**
            - `[p]embedset user False` - Disables embeds in your DMs.
            - `[p]embedset user` - Resets value to use global default.

        **Arguments:**
            - `[enabled]` - Whether to use embeds in your DMs. Leave blank to reset to default.
        """
        if enabled is None:
            await self.bot._config.user(ctx.author).embeds.clear()
            await ctx.send(_("Embeds will now fall back to the global setting."))
            return

        await self.bot._config.user(ctx.author).embeds.set(enabled)
        await ctx.send(
            _("Embeds are now enabled for you in DMs.")
            if enabled
            else _("Embeds are now disabled for you in DMs.")
        )
    
    def _check_if_command_requires_embed_links(self, command_obj: commands.Command) -> None:
        for command in itertools.chain((command_obj,), command_obj.parents):
            if command.requires.bot_perms.embed_links:
                # a slight abuse of this exception to save myself two lines later...
                raise commands.UserFeedbackCheckFailure(
                    _(
                        "The passed command requires Embed Links permission"
                        " and therefore cannot be set to not use embeds."
                    )
                )