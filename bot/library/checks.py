import lightbulb
from lightbulb import CheckFailure

class PlayerNotPlaying(CheckFailure):
    pass

class PlayerNotConnected(CheckFailure):
    pass

class NotInVoice(CheckFailure):
    pass

class NotSameVoice(CheckFailure):
    pass

@lightbulb.Check
def valid_user_voice(ctx: lightbulb.Context) -> bool:

    if not ctx.guild_id:
        raise lightbulb.CheckFailure('Cannot invoke command in DMs')
    
    states = ctx.app.cache.get_voice_states_view_for_guild(ctx.guild_id)
    user_voice_state = next(filter(lambda i : i[0] == ctx.author.id, states.items()), None)
    bot_voice_state = next(filter(lambda i: i[0] == ctx.app.get_me().id, states.items()), None)
    
    # if user & bot not in voice or in different channels
    if not user_voice_state:
        raise NotInVoice('Join voice channel to use command')
    if bot_voice_state and user_voice_state[1].channel_id != bot_voice_state[1].channel_id:
        raise NotSameVoice('Join the same channel as bot to use command')
    return True

@lightbulb.Check
def player_connected(ctx: lightbulb.Context) -> bool:

    player = ctx.app.d.lavalink.player_manager.get(ctx.guild_id)
    if not player or not player.is_connected:
        raise PlayerNotConnected('Bot is not in any voice channel')
    return True

@lightbulb.Check
def player_playing(ctx: lightbulb.Context) -> bool:

    player = ctx.app.d.lavalink.player_manager.get(ctx.guild_id)
    if not player or not player.is_playing:
        raise PlayerNotPlaying('Player is not playing')
    return True
