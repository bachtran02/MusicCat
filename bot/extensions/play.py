import hikari
import lavalink
import lightbulb

from bot.library.checks import valid_user_voice
from bot.library.base import _play, _get_tracks
from bot.library.classes.choice import AutocompleteChoice
from bot.library.classes.lavasearch import LavasearchResult
from bot.library.classes.sources import Source, Spotify, Deezer, YouTube
from bot.utils import trim

DELETE_AFTER = 60
SOURCES = [Spotify, Deezer, YouTube]
QUERY_TYPES = ['track', 'artist', 'playlist', 'album']

plugin = lightbulb.Plugin('Play', 'Commands to play music')

def play_checks_options(func: lightbulb.decorators.CommandCallbackT) -> lightbulb.decorators.CommandCallbackT:
    func = lightbulb.add_checks(lightbulb.guild_only, valid_user_voice)(func)
    func = lightbulb.option('loop', 'Loop track/playlist', choices=['True'], default='False')(func)
    func = lightbulb.option('next', 'Play track next', choices=['True'], default='False')(func)
    func = lightbulb.option('shuffle', 'Disable playlist shuffle', choices=['False'], default='True')(func)
    return func

async def get_choices(lavalink: lavalink.Client, query: str = None, types: str = None, source: Source = YouTube):

        if source == YouTube:
            result: lavalink.LoadResult = await _get_tracks(lavalink, query, YouTube)
            return [AutocompleteChoice('🎬 {} [{}]'.format(trim(track.title, 60), trim(track.author, 20)), track.uri) for track in result.tracks[:20]]

        if types:
            num_choices = 20
        else:
            types = 'track,artist,playlist,album'
            num_choices = 5

        query = f'{source.search_prefix}:{query}'
        node = lavalink.node_manager.find_ideal_node()
        json = await node._transport._request(
            method='GET',
            path='loadsearch',
            params={'query': query, 'types': types or 'track,artist,playlist,album'}
        )
        result = LavasearchResult.from_dict(json if isinstance(json, dict) else None)
        choices = []

        for track in result.tracks[:num_choices]:
            option = f'🎵 {trim(track.title, 60)} - {trim(track.author, 20)}'
            choices.append(AutocompleteChoice(name=option, value=track.uri))

        for item in result.artists[:num_choices]:
            option = f'🎤 {trim(item.author, 80)}'
            choices.append(AutocompleteChoice(name=option, value=item.uri))

        for item in result.playlists[:num_choices]:
            option = f'🎧 {trim(item.title, 60)} - {trim(item.author, 20)} ⭐'
            choices.append(AutocompleteChoice(name=option, value=item.uri))

        for item in result.albums[:num_choices]:
            option = f'💿 {trim(item.title, 60)} - {trim(item.author, 20)} 🎤'
            choices.append(AutocompleteChoice(name=option, value=item.uri))

        return choices

async def query_autocomplete(option, interaction):
   
    query = option.value
    if not query:
        return
    
    type_option = next(filter(lambda opt: opt.name == 'type', interaction.options), None)
    query_type = type_option.value if type_option else None
    
    for opt in interaction.options:
        name, value = opt.name, opt.value
        if name != 'source' and not query_type:
            continue
        if query_type or value in (Deezer.display_name, Spotify.display_name):
            source = Deezer if value == Deezer.display_name else Spotify
            return await get_choices(plugin.bot.d.lavalink, query, query_type, source)

    return await get_choices(plugin.bot.d.lavalink, query, YouTube)

async def handle_play(ctx: lightbulb.Context) -> None:
    
    result = await _get_tracks(lavalink=plugin.bot.d.lavalink, query=ctx.options.query)
    embed: hikari.Embed = await _play(
        bot=plugin.bot, 
        result=result, 
        guild_id=ctx.guild_id,
        author_id=ctx.author.id, 
        text_channel=ctx.channel_id,
        play_next=eval(ctx.options.next), 
        loop=eval(ctx.options.loop),
        shuffle=eval(ctx.options.shuffle)
    )
    if embed:
        await ctx.respond(embed=embed, delete_after=DELETE_AFTER)
    else:
        await ctx.respond('No result for query!', flags=hikari.MessageFlag.EPHEMERAL)

@plugin.command()
@play_checks_options
@lightbulb.option('query', 'Search query for track', required=True)
@lightbulb.command('play', 'Play track/playlist URL or search query on YouTube')
@lightbulb.implements(lightbulb.SlashCommand)
async def play(ctx: lightbulb.Context) -> None:
    """Play track URL or search query on YouTube"""
    await handle_play(ctx)

@plugin.command()
@play_checks_options
@lightbulb.option('source', 'Source to look up query', choices=[source.display_name for source in SOURCES], default=YouTube)
@lightbulb.option('type', 'Type of query', choices=QUERY_TYPES, default=None)
@lightbulb.option('query', 'Query to search for.', required=True, autocomplete=query_autocomplete)
@lightbulb.command('search', 'Search & add specific track/playlist to queue')
@lightbulb.implements(lightbulb.SlashCommand)
async def search(ctx: lightbulb.Context) -> None:
    """Precise track lookup via query autocomplete"""
    await handle_play(ctx)

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