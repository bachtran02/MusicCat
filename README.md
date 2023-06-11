# MusicCat

Another Discord Music Bot built with [hikari](https://www.hikari-py.dev/) and [lightbulb](https://hikari-lightbulb.readthedocs.io/en/latest/), inspired by project [Ashema](https://github.com/nauqh/Ashema) in collaboration with [Nauqh](https://github.com/nauqh)

  

# FEATURES:

* Intuitive slash commands `/` support 
* Enable YouTube query search / select from within Discord 

    `/search` `love me again john newman`
    
    <img src="https://user-images.githubusercontent.com/83796054/244956435-0cf6bb5f-3331-49f3-9779-7b82a84f6d88.png" width="450">

	
* Interactive Music Player: `/player`
    
    <img src="https://user-images.githubusercontent.com/83796054/244956842-c9ed0952-d7e0-45ac-9fa0-ad085638b990.png" width="450">


* Supports many sources (YouTube, SoundCloud, Spotify**) by using [Lavalink](https://github.com/lavalink-devs/Lavalink/tree/master) nodes



	> **Note**: Spotify is also supported, even though user needs to obtain their own `client_id` and `client_secret` from [Spotify](https://developer.spotify.com/dashboard) and input in  `Lavalinkserver/application.yml` to run

  
 
# COMMANDS:
Basic Music Commands:

Player

* /play - "Play track URL or search query on YouTube"

* /search - "Search & add specify query on YouTube"

* /skip

* /pause

* /resume

* /stop

* /seek

* /queue

* /now

Queue

* /remove - "Remove a track from queue"

* /shuffle - "Shuffle queue"

* /loop - "Loop current track or queue or end loop"


  

Other commands:

* /player - "Interactive guild player"

* /join

* /leave
