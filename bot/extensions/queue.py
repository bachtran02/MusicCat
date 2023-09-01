import hikari
import lightbulb

from bot.checks import valid_user_voice, player_playing
from bot.constants import COLOR_DICT
from bot.utils import format_time, player_bar
from bot.components import TrackSelectView

plugin = lightbulb.Plugin('Queue', 'Queue commands')


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, player_playing
)
@lightbulb.command('now', 'Display current track', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def now(ctx: lightbulb.Context) -> None:
    """Display current track"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

    desc = f'[{player.current.title}]({player.current.uri})'
    desc += '\n' + player_bar(player)
    desc += f'Requested - <@!{player.current.requester}>'

    await ctx.respond(
        embed=hikari.Embed(
            title = '🎵 Now Playing',
            description=desc, color=COLOR_DICT['GREEN']
        ).set_thumbnail(player.current.artwork_url))


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, player_playing,
)
@lightbulb.command('queue', 'Display the next 10 tracks in queue', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def queue(ctx : lightbulb.Context) -> None:
    """Display next (max 10) tracks in queue"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    
    desc = f'**Current:** [{player.current.title}]({player.current.uri})'
    desc += '\n' + player_bar(player)
    desc += f'Requested - <@!{player.current.requester}>' + '\n'

    for i in range(min(len(player.queue), 10)):
        if i == 0:
            desc += '\n' + '**Up next:**'
        track = player.queue[i]
        desc += '\n' + '{0}. [{1}]({2}) `{3}` <@!{4}>'.format(
            i+1, track.title, track.uri, format_time(track.duration), track.requester)

    await ctx.respond(embed=hikari.Embed(
        title = '🎵 Queue',
        description = desc,
        colour = COLOR_DICT['GREEN']))
    

@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing
)
@lightbulb.command('remove', 'Remove a track from queue', auto_defer = True)
@lightbulb.implements(lightbulb.SlashCommand)
async def remove(ctx: lightbulb.Context) -> None:
    """Remove a track from queue"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    if not player.queue:
        await ctx.respond('⚠️ Queue is emtpy!')
        return
    
    options = [f'{i + 1}. {track.title[:55]}' for i, track in enumerate(player.queue[:20])]
    view = TrackSelectView(select_options=options, timeout=60)
    view.build_track_select(placeholder='Select track to remove')

    message = await ctx.respond(components=view)
    await view.start(message)
    await view.wait()
    
    if (choice := view.get_choice()) == -1:
        await message.delete()
        return
        
    popped_track = player.queue.pop(choice - 1)
    await message.edit(
        components=None,
        embed=hikari.Embed(
            description = f'Removed: [{popped_track.title}]({popped_track.uri})',
            colour = COLOR_DICT['RED']
    ))


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)