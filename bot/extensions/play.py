import hikari
import lavalink
import lightbulb

from bot.library.checks import valid_user_voice
from bot.library.base import _play, _get_tracks, _get_autocomplete
from bot.library.classes.choice import AutocompleteChoice
from bot.library.classes.lavasearch import LavasearchResult
from bot.library.classes.sources import Spotify, Deezer, YouTube, YouTubeMusic

DELETE_AFTER = 60
plugin = lightbulb.Plugin('Play', 'Commands to play music')


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('query', 'Search query for track', required=True)
@lightbulb.option('loop', 'Loop track/playlist', choices=['True'], default='False')
@lightbulb.option('next', 'Play track next', choices=['True'], default='False')
@lightbulb.option('shuffle', 'Disable playlist shuffle', choices=['False'], default='True')
@lightbulb.command('play', 'Play track/playlist URL or search query on YouTube')
@lightbulb.implements(lightbulb.SlashCommand)
async def play(ctx: lightbulb.Context) -> None:
    """Play track URL or search query on YouTube"""
    
    result = await _get_tracks(lavalink=plugin.bot.d.lavalink, query=ctx.options.query)
    if (embed := await _play(
            bot=plugin.bot, result=result, guild_id=ctx.guild_id,
            author_id=ctx.author.id, text_channel=ctx.channel_id,
            play_next=eval(ctx.options.next), loop=eval(ctx.options.loop),
            shuffle=eval(ctx.options.shuffle))):
        await ctx.respond(embed=embed, delete_after=DELETE_AFTER)
    else:
        await ctx.respond('No result for query!', flags=hikari.MessageFlag.EPHEMERAL)

SOURCES = [Spotify, Deezer, YouTube, YouTubeMusic]
QUERY_TYPES = ['track', 'artist', 'playlist', 'album']
async def query_autocomplete(option, interaction):
   
    query = option.value    # partial query
    if not query:
        return
    
    num_choice = 5
    type_option = next(filter(lambda opt: opt.name == 'type', interaction.options), None)
    query_type = type_option.value if type_option else None
    
    for opt in interaction.options:
        name, value = opt.name, opt.value
        if name != 'source' and not query_type:
            continue
        if query_type or value in (Deezer.display_name, Spotify.display_name):
            num_choice = 20 if query_type else num_choice
            # when source is not specified, look up tracks on Deezer and everything else on Spotify 
            source = Deezer if value == Deezer.display_name or query_type == 'track' else Spotify
            raw = await _get_autocomplete(plugin.bot.d.lavalink, query, query_type, source)
            result = LavasearchResult.from_dict(raw)
            choices = []
            for track in result.tracks[:num_choice]:
                option, url = '🎵 {} - {}'.format(track.title, track.author), track.uri
                choices.append(AutocompleteChoice(name=option, value=url))
            for item in result.artists[:num_choice]:
                option, url = '🎤 {}'.format(item.author), item.uri
                choices.append(AutocompleteChoice(name=option, value=url))
            for item in result.playlists[:num_choice]:
                option, url = '🎧 {} - {} ⭐'.format(item.title, item.author), item.uri
                choices.append(AutocompleteChoice(name=option, value=url))
            for item in result.albums[:num_choice]:
                option, url = '💿 {} - {} 🎤'.format(item.title, item.author), item.uri
                choices.append(AutocompleteChoice(name=option, value=url))
            return choices
        if value == YouTubeMusic.source_name:
            result: lavalink.LoadResult = await _get_tracks(plugin.bot.d.lavalink, query, YouTubeMusic)
            return [AutocompleteChoice('🎵 {} - {}'.format(track.title[:60], track.author[:20]), track.uri) for track in result.tracks]
    result: lavalink.LoadResult = await _get_tracks(plugin.bot.d.lavalink, query, YouTube)
    return [AutocompleteChoice('🎬 {} [{}]'.format(track.title[:60], track.author[:20]), track.uri) for track in result.tracks]

@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('source', 'Source to look up query', choices=[source.display_name for source in SOURCES], default=None)
@lightbulb.option('type', 'Type of query', choices=QUERY_TYPES, default=None)
@lightbulb.option('query', 'Query to search for.', required=True, autocomplete=query_autocomplete)
@lightbulb.option('loop', 'Loop track/playlist', choices=['True'], default='False')
@lightbulb.option('next', 'Play track next', choices=['True'], default='False')
@lightbulb.option('shuffle', 'Disable playlist shuffle', choices=['False'], default='True')
@lightbulb.command('search', 'Search & add specific track/playlist to queue')
@lightbulb.implements(lightbulb.SlashCommand)
async def search(ctx: lightbulb.Context) -> None:

    result = await _get_tracks(lavalink=plugin.bot.d.lavalink, query=ctx.options.query)
    if (embed := await _play(
            bot=plugin.bot, result=result, guild_id=ctx.guild_id,
            author_id=ctx.author.id, text_channel=ctx.channel_id,
            play_next=eval(ctx.options.next), loop=eval(ctx.options.loop),
            shuffle=eval(ctx.options.shuffle))):
        await ctx.respond(embed=embed, delete_after=DELETE_AFTER)
    else:
        await ctx.respond('No result for query!', flags=hikari.MessageFlag.EPHEMERAL)

"""
@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.command('previous', 'Play previous track')
@lightbulb.implements(lightbulb.SlashCommand)
async def previous(ctx: lightbulb.Context) -> None:

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    await player.play_previous()
"""

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)