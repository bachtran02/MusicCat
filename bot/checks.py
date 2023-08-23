import lightbulb

@lightbulb.Check
def valid_user_voice(ctx: lightbulb.Context) -> bool:

    if not ctx.guild_id:
        raise lightbulb.CheckFailure('Cannot invoke command in DMs')
    
    states = ctx.app.cache.get_voice_states_view_for_guild(ctx.guild_id)
    user_voice_state = [state[1] for state in filter(lambda i : i[0] == ctx.author.id, states.items())]
    bot_voice_state = [state[1] for state in filter(lambda i: i[0] == ctx.app.get_me().id, states.items())]
    
    # if user & bot not in voice or in different channels
    if not user_voice_state:
        raise lightbulb.CheckFailure('Join voice channel to use command')
    if bot_voice_state and user_voice_state[0].channel_id != bot_voice_state[0].channel_id:
        raise lightbulb.CheckFailure('Join the same channel as bot to use command')
    return True

@lightbulb.Check
def player_connected(ctx: lightbulb.Context) -> bool:

    player = ctx.app.d.lavalink.player_manager.get(ctx.guild_id)
    if not player or not player.is_connected:
        raise lightbulb.CheckFailure('Bot is not in any voice channel')    
    return True

@lightbulb.Check
def player_playing(ctx: lightbulb.Context) -> bool:

    player = ctx.app.d.lavalink.player_manager.get(ctx.guild_id)
    if not player or not player.is_playing:
        raise lightbulb.CheckFailure('Player is not playing')
    return True
