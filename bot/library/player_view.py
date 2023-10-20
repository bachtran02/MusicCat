import hikari
import miru

from bot.constants import COLOR_DICT
from bot.utils import player_bar, track_display

class PlayerView(miru.View):

    EMPTY_EMBED = hikari.Embed(
        title='Nothing to play!',
        description='Play something',
        color=COLOR_DICT['YELLOW'])
    
    @staticmethod
    def get_embed(player) -> hikari.Embed:

        if not player or not player.is_playing:
            return PlayerView.EMPTY_EMBED

        return hikari.Embed(
            description='**Current:** {} \n {} \n Requested - <@!{}>'.format(
                track_display(player.current, exclude_duration=True),
                player_bar(player), player.current.requester),
            color=COLOR_DICT['GREEN']).set_thumbnail(player.current.artwork_url)
    
    def __init__(self) -> None:
        super().__init__(timeout=None)

    def get_player(self, guild_id: int):
        return self.bot.d.lavalink.player_manager.get(guild_id)
    
    @miru.button(style=hikari.ButtonStyle.SECONDARY, emoji='⏮️')
    async def play_backward(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        player = self.get_player(ctx.guild_id)
        await player.play_backward()
        await ctx.edit_response(embed=self.get_embed(player))

    @miru.button(style=hikari.ButtonStyle.SECONDARY, emoji='⏯️')
    async def play_pause(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        player = self.get_player(ctx.guild_id)
        await player.set_pause(not player.paused)
        await ctx.edit_response(embed=self.get_embed(player))

    @miru.button(style=hikari.ButtonStyle.SECONDARY, emoji='⏹️')
    async def stop(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        player = self.get_player(ctx.guild_id)
        await player.stop()
        await ctx.edit_response(embed=self.get_embed(player))

    @miru.button(style=hikari.ButtonStyle.SECONDARY, emoji='⏭️')
    async def skip(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        player = self.get_player(ctx.guild_id)
        await player.skip()
        await ctx.edit_response(embed=self.get_embed(player))

    # @miru.button(style=hikari.ButtonStyle.SECONDARY, emoji='❌')
    # async def remove(self, button: miru.Button, ctx: miru.ViewContext) -> None:
    #     await ctx.message.delete()
    #     self.stop()
