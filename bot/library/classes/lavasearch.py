from typing import List
from lavalink import AudioTrack

class SearchResultItem():

    def __init__(self, title: str = None, author: str = None, uri: str = None,
            artwork_url: str = None, type: str = None) -> None:
        self.title = title
        self.author = author
        self.uri = uri
        self.artwork_url = artwork_url
        self.type = type

    @classmethod
    def from_dict(cls, mapping: dict):
        plugin_info = mapping.get('pluginInfo', {})
        return cls(mapping.get('info', {}).get('name'), plugin_info.get('author'), plugin_info.get('url'),
            plugin_info.get('artworkUrl'), plugin_info.get('type'))

class LavasearchResult:

    ITEM_TYPE = {
        'tracks'    :  List[AudioTrack],
        'playlists' :  List[SearchResultItem],
        'artists'   :  List[SearchResultItem],
        'albums'    :  List[SearchResultItem],
    }

    def __init__(self, raw, tracks: List = [], albums: List = [], artists: List = [],
                playlists: List = [], texts: List = [], plugin = None):
        self.raw = raw
        self.tracks: List[AudioTrack] = [AudioTrack.from_dict(raw_track) for raw_track in tracks]
        self.albums: List[SearchResultItem] = [SearchResultItem.from_dict(raw_item) for raw_item in albums]
        self.artists: List[SearchResultItem] = [SearchResultItem.from_dict(raw_item) for raw_item in artists]
        self.playlists: List[SearchResultItem] = [SearchResultItem.from_dict(raw_item) for raw_item in playlists]

    @classmethod
    def from_dict(cls, mapping: dict):
        return cls(mapping, mapping.get('tracks'), mapping.get('albums'), mapping.get('artists'),
                   mapping.get('playlists'), mapping.get('texts'), mapping.get('plugin'))


