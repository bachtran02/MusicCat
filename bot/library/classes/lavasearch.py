from typing import List, Optional, Any
from lavalink import AudioTrack

class SearchResultItem:
    def __init__(self, title: Optional[str] = None, author: Optional[str] = None, uri: Optional[str] = None,
                 artwork_url: Optional[str] = None, item_type: Optional[str] = None) -> None:
        """
        Initialize a SearchResultItem instance.

        Args:
            title (Optional[str]): The title of the item.
            author (Optional[str]): The author of the item.
            uri (Optional[str]): The URI of the item.
            artwork_url (Optional[str]): The artwork URL of the item.
            item_type (Optional[str]): The type of the item.
        """
        self.title = title
        self.author = author
        self.uri = uri
        self.artwork_url = artwork_url
        self.item_type = item_type

    @classmethod
    def from_dict(cls, mapping: dict) -> 'SearchResultItem':
        """
        Create a SearchResultItem instance from a dictionary.

        Args:
            mapping (dict): The dictionary containing item data.

        Returns:
            SearchResultItem: The created SearchResultItem instance.
        """
        plugin_info = mapping.get('pluginInfo', {})
        return cls(
            title=mapping.get('info', {}).get('name'),
            author=plugin_info.get('author'),
            uri=plugin_info.get('url'),
            artwork_url=plugin_info.get('artworkUrl'),
            item_type=plugin_info.get('type')
        )

class LavasearchResult:

    def __init__(self, raw: Any, tracks: Optional[List[dict]] = None, albums: Optional[List[dict]] = None,
                 artists: Optional[List[dict]] = None, playlists: Optional[List[dict]] = None, 
                 texts: Optional[List[str]] = None, plugin: Optional[Any] = None) -> None:
        """
        Initialize a LavasearchResult instance.

        Args:
            raw (Any): The raw data.
            tracks (Optional[List[dict]]): List of raw track dictionaries. Defaults to None.
            albums (Optional[List[dict]]): List of raw album dictionaries. Defaults to None.
            artists (Optional[List[dict]]): List of raw artist dictionaries. Defaults to None.
            playlists (Optional[List[dict]]): List of raw playlist dictionaries. Defaults to None.
            texts (Optional[List[str]]): List of text data. Defaults to None.
            plugin (Optional[Any]): An optional plugin. Defaults to None.
        """
        self.raw = raw
        self.tracks: List[AudioTrack] = [AudioTrack.from_dict(raw_track) for raw_track in (tracks or [])]
        self.albums: List[SearchResultItem] = [SearchResultItem.from_dict(raw_item) for raw_item in (albums or [])]
        self.artists: List[SearchResultItem] = [SearchResultItem.from_dict(raw_item) for raw_item in (artists or [])]
        self.playlists: List[SearchResultItem] = [SearchResultItem.from_dict(raw_item) for raw_item in (playlists or [])]
        self.texts: List[str] = texts or []
        self.plugin = plugin

    @classmethod
    def from_dict(cls, mapping: dict) -> 'LavasearchResult':
        """
        Create a LavasearchResult instance from a dictionary.

        Args:
            mapping (dict): The dictionary containing search result data.

        Returns:
            LavasearchResult: The created LavasearchResult instance.
        """
        return cls(
            raw=mapping,
            tracks=mapping.get('tracks'),
            albums=mapping.get('albums'),
            artists=mapping.get('artists'),
            playlists=mapping.get('playlists'),
            texts=mapping.get('texts'),
            plugin=mapping.get('plugin')
        )