import miru
import hikari
import lavalink

from bot.constants import *
from bot.utils import format_time

def next_state(cur, mn, mx):
    while True:
        cur += 1
        if not cur in range(mn, mx + 1):
            cur = mn
        yield cur

        
class LoopButton(miru.Button):

    def __init__(self, player: lavalink.DefaultPlayer) -> None:
        super().__init__(
            row=1,
            style=hikari.ButtonStyle.SECONDARY,
            emoji=self.loop_icon(player.loop))
        self.loop = player.loop

    @staticmethod
    def loop_icon(loop: int):
        if loop == 0:
            return EMOJI_LOOP_OFF
        if loop == 1:
            return EMOJI_LOOP_QUEUE
        if loop == 2:
            return EMOJI_LOOP_TRACK
        
    async def callback(self, ctx: miru.ViewContext) -> None:
        
        it = next_state(self.loop, 0, 2)
        self.loop = next(it)
    
        self.view.get_player().set_loop(self.loop)
        self.emoji = self.loop_icon(self.loop)
        await self.view.update_message()

class ShuffleButton(miru.Button):

    def __init__(self, player: lavalink.DefaultPlayer) -> None:
        super().__init__(
            row=1,
            style=hikari.ButtonStyle.SECONDARY,
            emoji=self.shuffle_icon(player.shuffle))
        self.shuffle = player.shuffle

    @staticmethod
    def shuffle_icon(shuffle: int):
        if shuffle == 0:
            return EMOJI_SHUFFLE_OFF
        elif shuffle == 1:
            return EMOJI_SHUFFLE_ON
        
    async def callback(self, ctx: miru.ViewContext) -> None:
        
        it = next_state(self.shuffle, 0, 1)
        self.shuffle = next(it)
    
        self.view.get_player().set_shuffle(self.shuffle)
        self.emoji = self.shuffle_icon(self.shuffle)
        await self.view.update_message()

class PlayerView(miru.View):

    def __init__(self, guild_id: int) -> None:
        super().__init__(timeout=None)
        self.guild_id = guild_id

        self.add_item(LoopButton(self.get_player()))
        self.add_item(ShuffleButton(self.get_player()))

    def get_player(self) -> lavalink.DefaultPlayer:
        return self.bot.d.lavalink.player_manager.get(self.guild_id)
        
    @staticmethod
    def get_embed(player) -> hikari.Embed:

        assert player.is_playing is True
        
        current = player.current

        return hikari.Embed(
            description='[{}]({})\n{} `{}`\n\n<@!{}>'.format(
                current.title, current.uri, current.author,
                'LIVE' if current.stream else format_time(current.duration), 
                current.requester)).set_thumbnail(current.artwork_url)

    async def update_message(self):
        await self.message.edit(components=self)

    @miru.button(row=0, style=hikari.ButtonStyle.SECONDARY, emoji=EMOJI_PLAY_PREVIOUS)
    async def play_previous(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self.get_player().play_previous()

    @miru.button(row=0, style=hikari.ButtonStyle.SECONDARY, emoji=EMOJI_PAUSE_PLAYER)
    async def play_pause(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        
        player = self.get_player()
        await player.set_pause(not player.paused)
        button.emoji = EMOJI_RESUME_PLAYER if player.paused else EMOJI_PAUSE_PLAYER  
        await self.update_message()

    @miru.button(row=0, style=hikari.ButtonStyle.SECONDARY, emoji=EMOJI_PLAY_NEXT)
    async def play_next(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self.get_player().skip()
    
    @miru.button(row=1, style=hikari.ButtonStyle.SECONDARY, emoji=EMOJI_STOP_PLAYER)
    async def stop(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await self.get_player().stop()