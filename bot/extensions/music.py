import re
import logging
import asyncio

import lavalink
from lavalink import LoadType
import hikari
import lightbulb

from bot.impl import _join, _play, _search
from bot.checks import valid_user_voice, player_playing, player_connected
from bot.constants import COLOR_DICT, EFFECT_NIGHTCORE, EFFECT_BASS_BOOST
from bot.utils import format_time, player_bar
from bot.library.events import VoiceServerUpdate, VoiceStateUpdate
from bot.components import PlayerView, TrackSelectView

plugin = lightbulb.Plugin('Music', 'Basic music commands')


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
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command('join', 'Join the voice channel you are in.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def join(ctx: lightbulb.Context) -> None:
    """Join voice channel user is in"""
   
    try:
        player = await _join(plugin.bot, ctx.guild_id, ctx.author.id)
    except RuntimeError as error:
        await ctx.respond(f'⚠️ {error}')
    else:
        await ctx.respond(f'Joined <#{player.channel_id}>')


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_connected,
)
@lightbulb.command('leave', 'Leaves the voice channel the bot is in, clearing the queue.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def leave(ctx: lightbulb.Context) -> None:
    """Leave voice channel, clear guild player"""

    await plugin.bot.update_voice_state(ctx.guild_id, None)
    await ctx.respond('Left voice channel!')


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.command('skip', 'Skip the current song.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def skip(ctx: lightbulb.Context) -> None:
    """Skip the current song."""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    prev_track = await player.skip()

    await ctx.respond(embed=hikari.Embed(
        description = f'Skipped: [{prev_track.title}]({prev_track.uri})',
        colour = COLOR_DICT['RED']
    ))
    logging.info('Track skipped on guild: %s', ctx.guild_id)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.command('pause', 'Pause the current song.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def pause(ctx: lightbulb.Context) -> None:
    """Pause guild player"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    await player.set_pause(True)

    await ctx.respond(embed=hikari.Embed(
        description = '⏸️ Paused player',
        colour = COLOR_DICT['YELLOW']
    ))
    logging.info('Track paused on guild: %s', ctx.guild_id)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_connected,
)
@lightbulb.command('resume', 'Resume playing the current track', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def resume(ctx: lightbulb.Context) -> None:
    """Resume guild player"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    await player.set_pause(False)

    await ctx.respond(embed=hikari.Embed(
        description = '▶️ Resumed player',
        colour = COLOR_DICT['GREEN']
    ))
    logging.info('Track resumed on guild: %s', ctx.guild_id)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.command('stop', 'Stops the current song and clears queue.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def stop(ctx: lightbulb.Context) -> None:
    """Stop the guild player"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    await player.stop()

    await ctx.respond(embed=hikari.Embed(
        description = '⏹️ Stopped playing',
        colour = COLOR_DICT['RED']
    ))
    logging.info('Player stopped on guild: %s', ctx.guild_id)


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.command('restart', 'Restart current track', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def restart(ctx : lightbulb.Context) -> None:
    """Replay current track"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    if not player.current.is_seekable:
        await ctx.respond('⚠️ Current track is not seekable!')
        return
    await player.seek(0)

    await ctx.respond(embed=hikari.Embed(
        description = '⏩ Track restarted!',
        colour = COLOR_DICT['BLUE']
    ))


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.option('position', 'Position to seek (format: "[min]:[sec]" )', required=True)
@lightbulb.command('seek', "Seeks to a given position in the track", auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def seek(ctx : lightbulb.Context) -> None:
    """Seek to a position in a track"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    if not player.current.is_seekable:
        await ctx.respond('⚠️ Current track is not seekable!')
        return

    pos = ctx.options.position
    pos_rx = re.compile(r'\d+:\d{2}$')

    if not (pos_rx.match(pos) and int(pos.split(':')[1]) < 60):
        await ctx.respond('⚠️ Invalid position!')
        return
    
    (minute, second) = (int(x) for x in pos.split(':'))
    ms = minute * 60 * 1000 + second * 1000
    await player.seek(ms)

    await ctx.respond(embed=hikari.Embed(
        description = f'⏩ Player moved to `{minute}:{second:02}`',
        colour = COLOR_DICT['BLUE']
    ))


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.option('mode', 'Loop mode', choices=['track', 'queue', 'end'], required=False, default='track')
@lightbulb.command('loop', 'Loop current track or queue or end loop', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def loop(ctx:lightbulb.Context) -> None:
    """Loop current track or queue or end loop"""

    mode = ctx.options.mode
    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

    if mode == 'track':
        player.set_loop(1)
        body = '🔂 Enable Track loop!'
    elif mode == 'queue':
        player.set_loop(2)
        body = '🔁 Enable Queue loop!'
    else:
        player.set_loop(0)
        body = '⏭️ Disable loop!'
    
    await ctx.respond(embed=hikari.Embed(
        description = body,
        colour = COLOR_DICT['BLUE']
    ))


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only, valid_user_voice, player_playing,
)
@lightbulb.command('shuffle', 'Enable/disable shuffle', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def shuffle(ctx:lightbulb.Context) -> None:
    """Shuffle queue"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    player.set_shuffle(not player.shuffle)
   
    await ctx.respond(embed=hikari.Embed(
        description = f'🔀 {("Shuffle enabled" if player.shuffle else "Shuffle disabled")}',
        colour = COLOR_DICT['BLUE']
    ))


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
    lightbulb.guild_only, player_playing,
)
@lightbulb.option('effect', 'Effect to add', choices=['Bass Boost', 'Nightcore', 'None'], required=True)
@lightbulb.command('effects', 'Add music effect to player', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def effects(ctx : lightbulb.Context) -> None:
    """Add music effect to player"""

    effect = ctx.options.effect
    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)

    equalizer = lavalink.Equalizer()
    timescale = lavalink.Timescale()

    if effect == 'Bass Boost':
        equalizer.update(bands=EFFECT_BASS_BOOST['equalizer']['bands'])
    if effect == 'Nightcore':
        equalizer.update(bands=EFFECT_NIGHTCORE['equalizer']['bands'])
        timescale.update(
            pitch=EFFECT_NIGHTCORE['timescale']['pitch'],
            speed=EFFECT_NIGHTCORE['timescale']['speed'],
            rate=EFFECT_NIGHTCORE['timescale']['rate'],)
    if effect == 'None':
        await player.clear_filters()
        await ctx.respond(f'Effect cleared')
        return
    
    await player.set_filter(equalizer)
    await player.set_filter(timescale)
    await ctx.respond(f'Effect added: `{effect}`')
    logging.info('`%s` added to player on guild: %s', effect, ctx.guild_id)

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


@plugin.command()
@lightbulb.add_checks(
    lightbulb.guild_only,
)
@lightbulb.command('player', 'Interactive guild music player', auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def player(ctx: lightbulb.Context) -> None:
    """Interactive guild music player"""

    player = plugin.bot.d.lavalink.player_manager.get(ctx.guild_id)
    if not player or not player.is_playing:
        await ctx.respond('⚠️ Player is not playing!')
        return

    desc = f'**Streaming:** [{player.current.title}]({player.current.uri})'
    desc += '\n' + player_bar(player)
    desc += f'Requested - <@!{player.current.requester}>'

    view = PlayerView()

    message = await ctx.respond(
        components=view,
        embed=hikari.Embed(
            description=desc, color=COLOR_DICT['GREEN']
        ).set_thumbnail(player.current.artwork_url))

    await view.start(message)  # Start listening for interactions
    await view.wait()


@plugin.listener(hikari.VoiceServerUpdateEvent)
async def voice_server_update(event: hikari.VoiceServerUpdateEvent) -> None:
    await plugin.bot.d.lavalink._dispatch_event(VoiceServerUpdate(event))

@plugin.listener(hikari.VoiceStateUpdateEvent)
async def voice_state_update(event: hikari.VoiceStateUpdateEvent) -> None:
    await plugin.bot.d.lavalink._dispatch_event(VoiceStateUpdate(event))


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
