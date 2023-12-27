from lavalink import Event

class VoiceStateUpdate(Event):
    
    def __init__(self, event) -> None:
        self.prev_state = event.old_state
        self.cur_state = event.state
        self.guild_id = event.guild_id

class VoiceServerUpdate(Event):

    def __init__(self, event) -> None:
        self.guild_id = event.guild_id
        self.endpoint = event.endpoint[6:]
        self.token = event.token
