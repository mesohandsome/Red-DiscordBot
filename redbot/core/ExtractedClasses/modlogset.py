

class modlogset:
    async def __init__(self, ctx: commands.Context):
        pass
    
    async def fixcasetypes(self, ctx: commands.Context):
        """Command to fix misbehaving casetypes."""
        await modlog.handle_auditype_key()
        await ctx.tick()
    
    async def modlog(self, ctx: commands.Context, channel: Union[discord.TextChannel, discord.VoiceChannel]):
        """Set a channel as the modlog.

        Omit `[channel]` to disable the modlog.
        """
        guild = ctx.guild
        if channel:
            if channel.permissions_for(guild.me).send_messages:
                await modlog.set_modlog_channel(guild, channel)
                await ctx.send(
                    _("Mod events will be sent to {channel}.").format(channel=channel.mention)
                )
            else:
                await ctx.send(
                    _("I do not have permissions to send messages in {channel}!").format(
                        channel=channel.mention
                    )
                )
        else:
            try:
                await modlog.get_modlog_channel(guild)
            except RuntimeError:
                await ctx.send(_("Mod log is already disabled."))
            else:
                await modlog.set_modlog_channel(guild, None)
                await ctx.send(_("Mod log deactivated."))
    
    async def cases(self, ctx: commands.Context, action: str = None):
        """Enable or disable case creation for a mod action."""
        guild = ctx.guild

        if action is None:  # No args given
            casetypes = await modlog.get_all_casetypes(guild)
            await ctx.send_help()
            lines = []
            for ct in casetypes:
                enabled = _("enabled") if await ct.is_enabled() else _("disabled")
                lines.append(f"{ct.name} : {enabled}")

            await ctx.send(_("Current settings:\n") + box("\n".join(lines)))
            return

        casetype = await modlog.get_casetype(action, guild)
        if not casetype:
            await ctx.send(_("That action is not registered."))
        else:
            enabled = await casetype.is_enabled()
            await casetype.set_enabled(not enabled)
            await ctx.send(
                _("Case creation for {action_name} actions is now {enabled}.").format(
                    action_name=action, enabled=_("enabled") if not enabled else _("disabled")
                )
            )
    
    async def resetcases(self, ctx: commands.Context):
        """Reset all modlog cases in this server."""
        guild = ctx.guild
        await ctx.send(
            _("Are you sure you would like to reset all modlog cases in this server?")
            + " (yes/no)"
        )
        try:
            pred = MessagePredicate.yes_or_no(ctx, user=ctx.author)
            msg = await ctx.bot.wait_for("message", check=pred, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(_("You took too long to respond."))
            return
        if pred.result:
            await modlog.reset_cases(guild)
            await ctx.send(_("Cases have been reset."))
        else:
            await ctx.send(_("No changes have been made."))
    