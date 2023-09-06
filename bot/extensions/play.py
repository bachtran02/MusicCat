import hikari
import lavalink
import lightbulb

from bot.checks import valid_user_voice
from bot.impl import _play, _search
from bot.library.autocomplete_choice import AutocompleteChoice 

plugin = lightbulb.Plugin('Play', 'Commands to play music')


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('query', 'Search query for track', required=True)
@lightbulb.option('loop', 'Loop track', choices=['True'], required=False, default=False)
@lightbulb.option('next', 'Play the this track next', choices=['True'], required=False, default='False')
@lightbulb.option('shuffle', 'Shuffle playlist', choices=['False'], required=False, default='True')
@lightbulb.command('play', 'Play track URL or search query on YouTube')
@lightbulb.implements(lightbulb.SlashCommand)
async def play(ctx: lightbulb.Context) -> None:
    """Play track URL or search query on YouTube"""
    
    result: lavalink.LoadResult = await _search(lavalink=plugin.bot.d.lavalink, query=ctx.options.query)
    embed = await _play(
        bot=plugin.bot, guild_id=ctx.guild_id, author_id=ctx.author.id,
        result=result, text_id=ctx.channel_id, loop=(ctx.options.loop == 'True'),
        index=0 if ctx.options.next == 'True' else None, shuffle=(ctx.options.shuffle == 'True'),)
    if not embed:
        await ctx.respond('No result for query!', flags=hikari.MessageFlag.EPHEMERAL)
    else:
        await ctx.respond(embed=embed, delete_after=30)


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


async def query_autocomplete(option, interaction):
   
    query = option.value
    if not query:
        return None
    
    for opt in interaction.options:
        if opt.name == 'source' and opt.value == 'YouTube Music':
            result: lavalink.LoadResult = await plugin.bot.d.lavalink.get_tracks(query=f'ytmsearch:{query}')
            return [AutocompleteChoice(f'🎵 {track.title[:60]} - {track.author[:20]}', track.uri) for track in result.tracks]
    result: lavalink.LoadResult = await plugin.bot.d.lavalink.get_tracks(query=f'ytsearch:{query}')
    return [AutocompleteChoice(f'🎬 {track.title[:60]} [{track.author[:20]}]', track.uri) for track in result.tracks]

@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('source', 'Source to look up query', choices=['YouTube', 'YouTube Music'], default='YouTube')
@lightbulb.option('query', 'Query to search for.', required=True, autocomplete=query_autocomplete)
@lightbulb.command('search', 'Search & add specific YouTube/YouTube Music track to queue')
@lightbulb.implements(lightbulb.SlashCommand)
async def search(ctx: lightbulb.Context) -> None:

    result = await _search(lavalink=plugin.bot.d.lavalink, query=ctx.options.query)
    embed = await _play(
        bot=plugin.bot, result=result, guild_id=ctx.guild_id,
        author_id=ctx.author.id, text_id=ctx.channel_id,)
    if not embed:
        await ctx.respond('No result for query!', flags=hikari.MessageFlag.EPHEMERAL)
    else:
        await ctx.respond(embed=embed, delete_after=30)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)