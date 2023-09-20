import hikari
import lavalink
import lightbulb

from bot.checks import valid_user_voice
from bot.impl import _play, _search
from bot.library.autocomplete_choice import AutocompleteChoice
from bot.library.lavasearch import LavasearchResult

DELETE_AFTER = 60
plugin = lightbulb.Plugin('Play', 'Commands to play music')


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('query', 'Search query for track', required=True)
@lightbulb.option('loop', 'Loop track', choices=['True'], required=False, default=False)
@lightbulb.option('next', 'Play the this track next', choices=['True'], required=False, default='False')
@lightbulb.option('shuffle', 'Disable playlist shuffle', choices=['False'], required=False, default='True')
@lightbulb.command('play', 'Play track URL or search query on YouTube')
@lightbulb.implements(lightbulb.SlashCommand)
async def play(ctx: lightbulb.Context) -> None:
    """Play track URL or search query on YouTube"""
    
    result: lavalink.LoadResult = await _search(
        lavalink=plugin.bot.d.lavalink,
        query=ctx.options.query,
        search_prefix='ytsearch')
    if (embed := await _play(
            bot=plugin.bot, result=result, guild_id=ctx.guild_id,
            author_id=ctx.author.id, text_id=ctx.channel_id,
            options={
                'loop': ctx.options.loop,
                'next': ctx.options.next,
                'shuffle':ctx.options.shuffle})):
        await ctx.respond(embed=embed, delete_after=DELETE_AFTER)
    else:
        await ctx.respond('No result for query!', flags=hikari.MessageFlag.EPHEMERAL)


"""
@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('latest', 'Play newest tracks', choices=['True'], default=None, required=False)
@lightbulb.command('lnchill', 'Play random linhnhichill')
@lightbulb.implements(lightbulb.SlashCommand)
async def lnchill(ctx: lightbulb.Context) -> None:

    query = 'linhnhichill'
    query += ':latest' if ctx.options.latest else ''

    result = await _search(
        lavalink=plugin.bot.d.lavalink, 
        source='linhnhichill', query=query,
    )
    embed = await _play(
        bot=plugin.bot, result=result, guild_id=ctx.guild_id,
        author_id=ctx.author.id, text_id=ctx.channel_id,
    )
    await ctx.respond(embed=embed, delete_after=30)
"""

SOURCES = ['Spotify', 'YouTube', 'YouTube Music']
QUERY_TYPES = ['all', 'track', 'artist', 'playlist', 'album']
async def query_autocomplete(option, interaction):
   
    query = option.value    # partial query
    if not query:
        return None
    
    query_type, num_choice = 'all', 5
    for opt in interaction.options:
        if opt.name == 'type':
            query_type = opt.value
            break
    
    for opt in interaction.options:
        if opt.name != 'source' and query_type == 'all': 
            continue
        if query_type != 'all' or opt.value == 'Spotify':
            if query_type == 'all':
                query_type = 'track,artist,playlist,album'
            else:
                num_choice = 20
            raw = await plugin.bot.d.lavalink.search_tracks(query=f'spsearch:{query}', types=query_type)
            result = LavasearchResult.from_dict(raw)
            choices = []
            for track in result.tracks[:num_choice]:
                choice_name, url = f'🎵 {track.title} - {track.author}', track.uri
                choices.append(AutocompleteChoice(name=choice_name, value=url))
            for item in result.artists[:num_choice]:
                choice_name, url = f'🎤 {item.author}', item.uri
                choices.append(AutocompleteChoice(name=choice_name, value=url))
            for item in result.playlists[:num_choice]:
                choice_name, url = f'🎧 {item.title} - {item.author} 👑', item.uri
                choices.append(AutocompleteChoice(name=choice_name, value=url))
            for item in result.albums[:num_choice]:
                choice_name, url = f'💿 {item.title} - {item.author} 🎤', item.uri
                choices.append(AutocompleteChoice(name=choice_name, value=url))
            return choices
        if opt.value == 'YouTube Music':
            result: lavalink.LoadResult = await plugin.bot.d.lavalink.get_tracks(query=f'ytmsearch:{query}')
            return [AutocompleteChoice(f'🎵 {track.title[:60]} - {track.author[:20]}', track.uri) for track in result.tracks]
    result: lavalink.LoadResult = await plugin.bot.d.lavalink.get_tracks(query=f'ytsearch:{query}')
    return [AutocompleteChoice(f'🎬 {track.title[:60]} [{track.author[:20]}]', track.uri) for track in result.tracks]

@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('source', 'Source to look up query', choices=SOURCES, default='foo')
@lightbulb.option('type', 'Type of query', choices=QUERY_TYPES, default='all')
@lightbulb.option('query', 'Query to search for.', required=True, autocomplete=query_autocomplete)
@lightbulb.option('loop', 'Loop track', choices=['True'], required=False, default=False)
@lightbulb.option('next', 'Play the this track next', choices=['True'], required=False, default='False')
@lightbulb.option('shuffle', 'Disable playlist shuffle', choices=['False'], required=False, default='True')
@lightbulb.command('search', 'Search & add specific YouTube/YouTube Music track to queue')
@lightbulb.implements(lightbulb.SlashCommand)
async def search(ctx: lightbulb.Context) -> None:

    result = await _search(lavalink=plugin.bot.d.lavalink, query=ctx.options.query)
    if (embed := await _play(
            bot=plugin.bot, result=result, guild_id=ctx.guild_id,
            author_id=ctx.author.id, text_id=ctx.channel_id,
            options={
                'loop': ctx.options.loop,
                'next': ctx.options.next,
                'shuffle':ctx.options.shuffle})):
        await ctx.respond(embed=embed, delete_after=DELETE_AFTER)
    else:
        await ctx.respond('No result for query!', flags=hikari.MessageFlag.EPHEMERAL)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)