import re
import logging

import lavalink
import hikari
import lightbulb

from bot.checks import valid_user_voice, player_playing, player_connected
from bot.constants import COLOR_DICT, EFFECT_NIGHTCORE, EFFECT_BASS_BOOST
from bot.utils import player_bar
from bot.components import PlayerView


plugin = lightbulb.Plugin('Player', 'Player commands')

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


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
