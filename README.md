# MusicCat

A Discord music-playing bot built with [hikari](https://www.hikari-py.dev/) and [lightbulb](https://hikari-lightbulb.readthedocs.io/en/latest/). MusicCat uses [Lavalink](https://github.com/lavalink-devs/Lavalink/tree/master) as audio source and its plugins for additional features. 

### Invite the bot here: [Invite URL](https://discord.com/api/oauth2/authorize?client_id=1055170653126398013&permissions=0&scope=bot)


## NOTABLE FEATURES:

* Intuitive Discord slash commands `/` support.
* `/search` - Search query autocompletion allows precise track lookup: 
	* `type` - type of query (track/artist/playlist/album).
	* `source` - search source to look up query (YouTube/YouTube Music/Spotify).

<img src="https://github.com/bachtran02/MusicCat/assets/83796054/68241e7a-469a-4213-b10b-84ba1fbe03c6" width="400">
 <img src="https://github.com/bachtran02/MusicCat/assets/83796054/baf96170-0f61-4fb8-b4ed-e40123d3439e" width="400">

* `/player` - Interactive and persistent music player allows better control of playing music with buttons.
    
    <img src="https://github.com/bachtran02/MusicCat/assets/83796054/0bc24fd1-be0f-49ae-97cf-5abe3acff2ef" width="450">

* `/effects` - add effects to your music (currently supports `Nightcore` and `Bass Boosted`).

* Personal music `play/pause` support - when the voice session only has you and the bot, Discord's `deafen` 🎧 pauses the player and `undeafen` resumes it.
* Sources supported: [YouTube](https://www.youtube.com/), [YouTube Music](https://music.youtube.com/), [Spotify](https://open.spotify.com/), and more [here](https://github.com/lavalink-devs/lavaplayer#supported-formats) 
* 24/7 Support :) 

> Any suggestion for cool additional features feel free to reach out!


### Slash (/) command list:
Track lookup:	`play` `search`

Player control: `pause` `resume` `skip` `stop` `seek` `restart` 

Queue: `now` `queue` `remove` `shuffle` `loop` 

Effects: `effects` 

Player: `player`

Others: `join` `leave` `mute` `unmute` 

> `remove` for removing a track from queue also has autocomplete support 
>
> `mute`/`unmute` to enable/disable sending message on track starts


---
Inspired by project [Ashema](https://github.com/nauqh/Ashema) in collaboration with [Nauqh](https://github.com/nauqh)
