package musicbot

import (
	"sync"

	"github.com/disgoorg/disgolink/v3/disgolink"
	"github.com/disgoorg/snowflake/v2"
)

// PlayerManager manages all the active guild players.
type PlayerManager struct {
	// We need a reference to the disgolink client to create new players.
	link disgolink.Client

	players map[snowflake.ID]*Player
	mu      sync.RWMutex
}

// NewPlayerManager creates a new, empty PlayerManager.
func NewPlayerManager(link disgolink.Client) *PlayerManager {
	return &PlayerManager{
		link:    link,
		players: make(map[snowflake.ID]*Player),
	}
}

// GetPlayer retrieves an existing player for a guild.
func (pm *PlayerManager) GetPlayer(guildID snowflake.ID) (*Player, bool) {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	player, ok := pm.players[guildID]
	return player, ok
}

/* Retrieves an existing player or creates a new one. */
func (pm *PlayerManager) GetOrCreatePlayer(guildID snowflake.ID) *Player {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	player, ok := pm.players[guildID]
	if ok {
		/* player already existed */
		return player
	}

	/* Get the underlying disgolink player for the guild. */
	linkPlayer := pm.link.Player(guildID)

	/* Create our new player controller. */
	player = NewPlayer(guildID, linkPlayer)
	pm.players[guildID] = player

	return player
}

// DeletePlayer removes a player for a guild.
// This should be called when the bot disconnects from a voice channel.
func (pm *PlayerManager) DeletePlayer(guildID snowflake.ID) {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	delete(pm.players, guildID)
}
