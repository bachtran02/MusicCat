import random
import lightbulb

from bot.impl import _join, _play, _search
from bot.constants import BASE_YT_URL
from bot.checks import valid_user_voice

plugin = lightbulb.Plugin('Uncommon', 'Uncommon personal music commands')

@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice,
)
@lightbulb.option('latest', 'Play newest tracks', choices=['True'], default=None, required=False)
@lightbulb.command('chill', 'Play random linhnhichill', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def chill(ctx: lightbulb.Context) -> None:

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    if not player or not player.is_connected:
        player = await _join(plugin.bot, ctx.guild_id, ctx.author.id)

    if ctx.options.latest:
        search = plugin.bot.d.yt.search().list(
            part='snippet', type='video',
            channelId='UCOGDtlp0av6Cp366BGS_PLQ',
            order='date', maxResults=10,
        ).execute()

        if not (isinstance(search, dict) or search.get('items', None)):
            await ctx.respond('⚠️ Failed to search for latest tracks')
            return
        
        yid = search['items'][random.randrange(len(search['items']))]['id']['videoId']
        results = await player.node.get_tracks(f'{BASE_YT_URL}/watch?v={yid}')

        if not results.load_type == 'TRACK_LOADED':
            await ctx.respond('⚠️ Failed to load track')
            return
        track = results.tracks[0]
    else:
        query = f'{BASE_YT_URL}/playlist?list=PL-F2EKRbzrNQte4aGjHp9cQau9peyPMw0'
        results = await _search(plugin.bot.d.lavalink, query=query)
        if not results:
            await ctx.respond('⚠️ Failed to find playlist')
        track = results['tracks'][random.randrange(len(results['tracks']))]
    
    embed = await _play(
        bot=plugin.bot, guild_id=ctx.guild_id, author_id=ctx.author.id,
        query=track, textchannel=ctx.channel_id, autoplay=False,
    )
    await ctx.respond(embed=embed)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
