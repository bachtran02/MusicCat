import hikari
import miru

from hikari.emojis import CustomEmoji

from bot.constants import *
from bot.utils import format_time

class PlayerView(miru.View):
    
    @staticmethod
    def get_embed(player) -> hikari.Embed:

        assert player.is_playing is True
        
        current = player.current
        
        return hikari.Embed(
            description='[{}]({})\n{} `{}`\n\n<@!{}>'.format(
                current.title, current.uri, current.author,
                'LIVE' if current.stream else format_time(current.duration), 
                current.requester)
        ).set_thumbnail(player.current.artwork_url)
    
    def __init__(self) -> None:
        super().__init__(timeout=None)

    def get_player(self, guild_id: int):
        return self.bot.d.lavalink.player_manager.get(guild_id)

    async def update_message(self):
        await self.message.edit(components=self)
    
    @miru.button(style=hikari.ButtonStyle.SECONDARY, emoji=CustomEmoji.parse(EMOJI_PLAY_PREVIOUS))
    async def play_previous(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        player = self.get_player(ctx.guild_id)
        await player.play_previous()

    @miru.button(style=hikari.ButtonStyle.SECONDARY, emoji=CustomEmoji.parse(EMOJI_PAUSE_PLAYER))
    async def play_pause(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        
        player = self.get_player(ctx.guild_id)
        await player.set_pause(not player.paused)
        emoji = EMOJI_RESUME_PLAYER if player.paused else EMOJI_PAUSE_PLAYER
        button.emoji = CustomEmoji.parse(emoji)
        await self.update_message()

    @miru.button(style=hikari.ButtonStyle.SECONDARY, emoji=CustomEmoji.parse(EMOJI_STOP_PLAYER))
    async def stop(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        player = self.get_player(ctx.guild_id)
        await player.stop()

    @miru.button(style=hikari.ButtonStyle.SECONDARY, emoji=CustomEmoji.parse(EMOJI_PLAY_NEXT))
    async def play_next(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        player = self.get_player(ctx.guild_id)
        await player.skip()