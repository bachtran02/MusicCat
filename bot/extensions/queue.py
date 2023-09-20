import hikari
import lightbulb

from bot.checks import valid_user_voice, player_playing
from bot.constants import COLOR_DICT
from bot.utils import format_time, player_bar
from bot.library.autocomplete_choice import AutocompleteChoice 

DELETE_AFTER = 60
plugin = lightbulb.Plugin('Queue', 'Queue commands')


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, player_playing
)
@lightbulb.command('now', 'Display current track')
@lightbulb.implements(lightbulb.SlashCommand)
async def now(ctx: lightbulb.Context) -> None:
    """Display current track"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

    desc = f'[{player.current.title}]({player.current.uri})\n'
    desc += player_bar(player) + '\n'
    desc += f'Requested - <@!{player.current.requester}>\n'

    await ctx.respond(
        embed=hikari.Embed(
            title = '🎵 Now Playing',
            description=desc, color=COLOR_DICT['GREEN']
        ).set_thumbnail(player.current.artwork_url))


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, player_playing,
)
@lightbulb.command('queue', 'Display the next 10 tracks in queue')
@lightbulb.implements(lightbulb.SlashCommand)
async def queue(ctx : lightbulb.Context) -> None:
    """Display next (max 10) tracks in queue"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    
    desc = f'**Current:** [{player.current.title}]({player.current.uri})\n'
    desc += player_bar(player) + '\n'
    desc += f'Requested - <@!{player.current.requester}>\n\n'

    for i in range(min(len(player.queue), 10)):
        if i == 0:
            desc += '**Up next:**'
        track = player.queue[i]
        desc += '\n' + '{0}. [{1}]({2}) `{3}` <@!{4}>'.format(
            i+1, track.title, track.uri, format_time(track.duration), track.requester)

    await ctx.respond(
        embed=hikari.Embed(
            title = '🎵 Queue',
            description = desc,
            colour = COLOR_DICT['GREEN']
        ).set_thumbnail(player.current.artwork_url))
    

async def remove_autocomplete(option, interaction):
    
    player = plugin.bot.d.lavalink.player_manager.get(interaction.guild_id)
    if not player or not player.is_playing:
        return None
    return [AutocompleteChoice(f'{track.title[:60]} - {track.author[:20]}', str(i)) for i, track in enumerate(player.queue[:25])]

@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing
)
@lightbulb.option('track', 'Track to remove', required=True, autocomplete=remove_autocomplete)
@lightbulb.command('remove', 'Remove a track from queue')
@lightbulb.implements(lightbulb.SlashCommand)
async def remove(ctx: lightbulb.Context) -> None:
    """Remove a track from queue"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    index = ctx.options.track
    popped_track = player.queue.pop(int(index))

    await ctx.respond(
        embed=hikari.Embed(
            description = f'Removed: [{popped_track.title}]({popped_track.uri})',
            colour = COLOR_DICT['RED']), delete_after=DELETE_AFTER)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)