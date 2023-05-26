import typing as t

import hikari
import miru
import lavalink

from bot.constants import COLOR_DICT
from bot.utils import player_bar

class PlayerView(miru.View):

    def get_player(self, guild_id: int) -> lavalink.DefaultPlayer:
        return self.bot.d.lavalink.player_manager.get(guild_id)
    
    def get_player_embed(self, player: lavalink.DefaultPlayer = None):

        if not player.current:
            return hikari.Embed(
                description='Queue is empty! Play some music 🎶',
                color=COLOR_DICT['YELLOW']
            )
        desc = f'**Streaming:** [{player.current.title}]({player.current.uri})' +'\n'
        desc += player_bar(player)
        desc += f'Requested - <@!{player.current.requester}>'

        return hikari.Embed(
            description=desc,
            color=COLOR_DICT['GREEN']
        ).set_thumbnail(player.current.artwork_url)
        
    @miru.button(style=hikari.ButtonStyle.SECONDARY, emoji='⏮️')
    async def previous(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        player = self.get_player(ctx.guild_id)

    @miru.button(style=hikari.ButtonStyle.SECONDARY, emoji='⏯️')
    async def playplause(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        player = self.get_player(ctx.guild_id)
        await player.set_pause(not player.paused)
        await ctx.edit_response(embed=self.get_player_embed(player))

    @miru.button(style=hikari.ButtonStyle.SECONDARY, emoji='⏹️')
    async def stop(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        player = self.get_player(ctx.guild_id)
        await player.stop()
        await self.bot.update_presence(activity=None) # clear presence
        await ctx.edit_response(embed=self.get_player_embed(player))

    @miru.button(style=hikari.ButtonStyle.SECONDARY, emoji='⏭️')
    async def next(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        player = self.get_player(ctx.guild_id)
        await player.skip()
        await ctx.edit_response(embed=self.get_player_embed(player))

    @miru.button(style=hikari.ButtonStyle.SECONDARY, emoji='❌')
    async def remove(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await ctx.message.delete()
        self.stop()

class CustomTextSelect(miru.TextSelect):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
    
    async def callback(self, ctx: miru.ViewContext) -> None:
        self.view.choice = self.values[0]
        self.view.stop()

class RemoveButton(miru.Button):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def callback(self, ctx: miru.ViewContext) -> None:
        self.view.stop()