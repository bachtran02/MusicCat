# MusicCat

A Discord music-playing bot built with [hikari](https://www.hikari-py.dev/) and [lightbulb](https://hikari-lightbulb.readthedocs.io/en/latest/). MusicCat uses [Lavalink](https://github.com/lavalink-devs/Lavalink/tree/master) as audio source and [Lavalink.py](https://github.com/Devoxin/Lavalink.py) (custom branch) as wrapper for Lavalink. 

MusicCat runs in Docker container hosted by my Raspberry Pi with the desired uptime 24/7. 
More information on how this repo can be forked and run locally will be added! 

---

## FEATURES:

* Intuitive slash commands `/` support 
* Enable YouTube query search / select from within Discord 

    `/search` `love me again john newman`
    
    <img src="https://user-images.githubusercontent.com/83796054/244956435-0cf6bb5f-3331-49f3-9779-7b82a84f6d88.png" width="450">

	
* Interactive Music Player: `/player`
    
    <img src="https://user-images.githubusercontent.com/83796054/244956842-c9ed0952-d7e0-45ac-9fa0-ad085638b990.png" width="450">


* Support many sources (YouTube, SoundCloud, Spotify**) by using [Lavalink](https://github.com/lavalink-devs/Lavalink/tree/master) nodes

	> **Note**: Spotify is also supported, even though user needs to obtain their own `client_id` and `client_secret` from [Spotify](https://developer.spotify.com/dashboard) and input in  `Lavalinkserver/application.yml` to run

  
## COMMANDS:

#### Music Player Commands

* `/play` - Play track URL or search query on YouTube

* `/search`  - Search & add specify query on YouTube

* `/skip`

* `/pause`

* `/resume`

* `/stop`

* `/seek`

* `/queue`

* `/now`

* `/player` - Interactive music player

#### Queue Commands

* `/shuffle` 

* `/loop`

* `/remove` - Remove a track from queue


#### Other commands:

* `/join`

* `/leave`


---
Inspired by project [Ashema](https://github.com/nauqh/Ashema) in collaboration with [Nauqh](https://github.com/nauqh)
