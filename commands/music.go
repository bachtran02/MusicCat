package commands

import (
	"github.com/disgoorg/disgo/discord"
)

var searchTypeChoices = []discord.ApplicationCommandOptionChoiceString{
	{
		Name:  "Track",
		Value: "track",
	},
	{
		Name:  "Album",
		Value: "album",
	},
	{
		Name:  "Artist",
		Value: "artist",
	},
	{
		Name:  "Playlist",
		Value: "playlist",
	},
}

var searchSourceChoices = []discord.ApplicationCommandOptionChoiceString{
	{
		Name:  "YouTube",
		Value: "youtube",
	},
	{
		Name:  "Deezer",
		Value: "deezer",
	},
	{
		Name:  "Spotify",
		Value: "spotify",
	},
}

var loopModeChoices = []discord.ApplicationCommandOptionChoiceString{
	{
		Name:  "none",
		Value: "none",
	},
	{
		Name:  "track",
		Value: "track",
	},
	{
		Name:  "queue",
		Value: "queue",
	},
}

var music = discord.SlashCommandCreate{
	Name:        "music",
	Description: "music commands",
	Options: []discord.ApplicationCommandOption{
		discord.ApplicationCommandOptionSubCommand{
			Name:        "play",
			Description: "Play a song from query",
			Options: []discord.ApplicationCommandOption{
				discord.ApplicationCommandOptionString{
					Name:        "query",
					Description: "Search query for track",
					Required:    true,
				},
				discord.ApplicationCommandOptionBool{
					Name:        "next",
					Description: "Play query next in",
					Required:    false,
				},
				discord.ApplicationCommandOptionBool{
					Name:        "loop",
					Description: "Enable loop for query",
					Required:    false,
				},
				discord.ApplicationCommandOptionBool{
					Name:        "shuffle",
					Description: "Enable shuffle for query",
					Required:    false,
				},
			}},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "search",
			Description: "Add & play track/playlist from search results",
			Options: []discord.ApplicationCommandOption{
				discord.ApplicationCommandOptionString{
					Name:         "query",
					Description:  "Search query for track",
					Required:     true,
					Autocomplete: true,
				},
				discord.ApplicationCommandOptionString{
					Name:        "source",
					Description: "The source to search from",
					Required:    false,
					Choices:     searchSourceChoices,
				},
				discord.ApplicationCommandOptionString{
					Name:        "type",
					Description: "The type of the search",
					Required:    false,
					Choices:     searchTypeChoices,
				},
				discord.ApplicationCommandOptionBool{
					Name:        "next",
					Description: "Play query next in",
					Required:    false,
				},
				discord.ApplicationCommandOptionBool{
					Name:        "loop",
					Description: "Enable loop for query",
					Required:    false,
				},
				discord.ApplicationCommandOptionBool{
					Name:        "shuffle",
					Description: "Enable shuffle for query",
					Required:    false,
				},
			}},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "playlist",
			Description: "Add & play your saved playlists",
			Options: []discord.ApplicationCommandOption{
				discord.ApplicationCommandOptionInt{
					Name:         "playlist",
					Description:  "Playlist name",
					Required:     true,
					Autocomplete: true,
				},
				discord.ApplicationCommandOptionBool{
					Name:        "next",
					Description: "Play query next in queue",
					Required:    false,
				},
				discord.ApplicationCommandOptionBool{
					Name:        "loop",
					Description: "Enable loop for query",
					Required:    false,
				},
				discord.ApplicationCommandOptionBool{
					Name:        "shuffle",
					Description: "Enable shuffle for query",
					Required:    false,
				},
			}},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "queue",
			Description: "Display queue",
		},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "resume",
			Description: "Resume player",
		},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "pause",
			Description: "Pause player",
		},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "now",
			Description: "Current track",
		},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "stop",
			Description: "Stop player",
		},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "skip",
			Description: "Skip current track",
		},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "shuffle",
			Description: "Shuffle queue",
		},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "loop",
			Description: "Loop track/queue",
			Options: []discord.ApplicationCommandOption{
				discord.ApplicationCommandOptionString{
					Name:        "mode",
					Description: "Loop mode",
					Required:    true,
					Choices:     loopModeChoices,
				},
			},
		},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "seek",
			Description: "Seek player to a position",
			Options: []discord.ApplicationCommandOption{
				discord.ApplicationCommandOptionString{
					Name:        "position",
					Description: "Postion to seek to (format: [HH:MM:SS] or [MM:SS])",
					Required:    true,
				},
			},
		},
		discord.ApplicationCommandOptionSubCommand{
			Name:        "remove",
			Description: "Remove track from queue",
			Options: []discord.ApplicationCommandOption{
				discord.ApplicationCommandOptionInt{
					Name:         "track",
					Description:  "Track to remove from queue",
					Required:     true,
					Autocomplete: true,
				},
			},
		},
	},
}
