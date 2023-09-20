import typing as t

import lavalink
from lightbulb.utils import DataStore

class GuildDataStore():
    
    def __init__(self, channel_id: int = None, track_loop: bool = False, send_nowplaying : bool = True) -> None:
        self.channel_id = channel_id            # text channel to send now_playing info
        self.track_loop = track_loop            # to avoid sending now_playing in track loop
        self.send_nowplaying = send_nowplaying  # whether to send now_playing

    def clear(self):
        self.track_loop, self.send_nowplaying = False, True

class BotDataStore():

    def __init__(self, lavalink: lavalink.Client) -> None:
        self.lavalink = lavalink
        self.guilds: t.Dict[str, GuildDataStore] = {}

    def to_datastore(self) -> DataStore:
        return DataStore(self.__dict__)