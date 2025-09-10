package commands

import (
	"MusicCatGo/musicbot"

	"github.com/disgoorg/disgo/discord"
)

var CommandCreates = []discord.ApplicationCommandCreate{
	bot,
	music,
	playlist,
}

type Commands struct {
	*musicbot.Bot
}
