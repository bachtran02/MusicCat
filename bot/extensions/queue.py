import hikari
import lightbulb

from bot.library.checks import valid_user_voice, player_playing
from bot.library.classes.choice import AutocompleteChoice 
from bot.library.classes.sources import Spotify, Deezer
from bot.utils import player_bar, format_time

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
    current = player.current

    desc = '[{}]({})\n{}\n{}\n\nRequested: <@!{}>\n'.format(
        current.title, current.uri, current.author,
        player_bar(player), current.requester)
    
    if player.queue:
        track = player.queue[0]
        desc += '\n**Up next:**\n[{}]({}) `{}`'.format(
            track.title, track.uri,
            'LIVE' if track.stream else format_time(track.duration))
        if track.source_name in (source.source_name.lower() for source in (Deezer, Spotify)):
            desc += f' {track.author}'

    await ctx.respond(
        embed=hikari.Embed(
            title = '🎵 Now Playing',
            description=desc).set_thumbnail(current.artwork_url))

@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, player_playing,
)
@lightbulb.command('queue', 'Display the next 10 tracks in queue')
@lightbulb.implements(lightbulb.SlashCommand)
async def queue(ctx : lightbulb.Context) -> None:
    """Display next (max 10) tracks in queue"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    current = player.current

    desc = '[{}]({})\n{}\n{}\n\nRequested: <@!{}>\n'.format(
        current.title, current.uri, current.author,
        player_bar(player), current.requester)

    for i, track in enumerate(player.queue):
        if i == 0:
            desc += '\n**Up next:**'
        if i >= 10:
            break

        desc += '\n{}. [{}]({}) `{}`'.format(
            i + 1, track.title, track.uri,
            'LIVE' if track.stream else format_time(track.duration))
        if track.source_name in (source.source_name.lower() for source in (Deezer, Spotify)):
            desc += f' {track.author}'

    await ctx.respond(
        embed=hikari.Embed(
            title = '🎵 Queue',
            description = desc,
        ).set_thumbnail(current.artwork_url))

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

    index = ctx.options.track
    if not index.isdigit():
        await ctx.respond('Queue empty - Nothing to remove!', flags=hikari.MessageFlag.EPHEMERAL)
        return

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    popped_track = player.queue.pop(int(index))

    await ctx.respond(
        embed=hikari.Embed(
            description = f'Removed: [{popped_track.title}]({popped_track.uri})'),
            delete_after=DELETE_AFTER)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)