import asyncio

import lavalink
from lavalink import LoadType
import hikari
import lightbulb

from bot.impl import _play, _search
from bot.checks import valid_user_voice
from bot.constants import COLOR_DICT
from bot.components import TrackSelectView

plugin = lightbulb.Plugin('Play', 'Commands to play music')


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('query', 'Search query for track', modifier=lightbulb.OptionModifier.CONSUME_REST, required=True)
@lightbulb.option('loop', 'Loop track', choices=['True'], required=False, default=False)
@lightbulb.option('next', 'Play the this track next', choices=['True'], required=False, default='False')
@lightbulb.option('shuffle', 'Shuffle playlist', choices=['False'], required=False, default='True')
@lightbulb.command('play', 'Play track URL or search query on YouTube', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def play(ctx: lightbulb.Context) -> None:
    """Play track URL or search query on YouTube"""

    query = ctx.options.query
    
    result: lavalink.LoadResult = await _search(lavalink=plugin.bot.d.lavalink, query=query)
    embed = await _play(
        bot=plugin.bot, guild_id=ctx.guild_id, author_id=ctx.author.id,
        result=result, text_id=ctx.channel_id, loop=(ctx.options.loop == 'True'),
        index=0 if ctx.options.next == 'True' else None, shuffle=(ctx.options.shuffle == 'True'),)
    if not embed:
        await ctx.respond('⚠️ No result for query!', delete_after=30)
    else:
        await ctx.respond(embed=embed, delete_after=30)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('latest', 'Play newest tracks', choices=['True'], default=None, required=False)
@lightbulb.command('lnchill', 'Play random linhnhichill', auto_defer=True)
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


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('query', 'The query to search for.', modifier=lightbulb.OptionModifier.CONSUME_REST, required=True)
@lightbulb.command('search', 'Search & add specific YouTube track to queue', auto_defer = True)
@lightbulb.implements(lightbulb.SlashCommand)
async def search(ctx: lightbulb.Context) -> None:

    query = ctx.options.query

    result = await _search(lavalink=plugin.bot.d.lavalink, query=query)
    if result.load_type != LoadType.SEARCH:
        await ctx.respond('⚠️ Failed to load search result for query!', delete_after=30)
        return

    options = [f'{i + 1}. {track.title[:55]}' for i, track in enumerate(result.tracks[:20])]
    view = TrackSelectView(select_options=options, timeout=60)
    view.build_track_select(placeholder='Select track to play')

    message = await ctx.respond(
        components=view,
        embed=hikari.Embed(
            color=COLOR_DICT['GREEN'],
            description=f'🔍 **Search results for:** `{query}`',
        ))
    
    await view.start(message)
    await view.wait()

    if (choice := view.get_choice()) == -1:
        await message.delete()
        return
    
    result.load_type = LoadType.TRACK
    result.tracks = [result.tracks[choice - 1]]

    embed = await _play(
        bot=plugin.bot, result=result, guild_id=ctx.guild_id,
        author_id=ctx.author.id, text_id=ctx.channel_id,)
    await message.edit(embed=embed, components=None)
    await asyncio.sleep(30)
    await message.delete()


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)