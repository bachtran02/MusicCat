package handlers

import (
	"MusicCatGo/musicbot"
	"encoding/json"
	"net/http"
	"sync"

	"github.com/disgoorg/disgolink/v3/disgolink"
	"github.com/disgoorg/disgolink/v3/lavalink"
	"github.com/disgoorg/snowflake/v2"
)

type TrackerResponse struct {
	IsPlaying bool               `json:"is_playing"`
	IsPaused  bool               `json:"is_paused,omitempty"`
	TrackInfo lavalink.TrackInfo `json:"track,omitempty"`
}

type TrackerHandler struct {
	ChannelID snowflake.ID
	GuildID   snowflake.ID
	WsServer  *musicbot.WsServer
	track     lavalink.Track
	isPlaying bool
	isPaused  bool
	mutex     sync.Mutex
}

func (h *TrackerHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	h.mutex.Lock()
	defer h.mutex.Unlock()

	response := TrackerResponse{
		IsPlaying: h.isPlaying,
	}
	if h.isPlaying {
		response.TrackInfo = h.track.Info
	}

	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}

func (h *TrackerHandler) broadcastUpdate() {
	jsonResponse, err := json.Marshal(
		TrackerResponse{
			IsPlaying: h.isPlaying,
			IsPaused:  h.isPaused,
			TrackInfo: h.track.Info,
		})
	if err != nil {
		return
	}
	h.WsServer.Broadcast <- jsonResponse
}

func (h *TrackerHandler) OnTrackStart(p disgolink.Player, event lavalink.TrackStartEvent) {
	h.mutex.Lock()
	defer h.mutex.Unlock()
	if p.GuildID() == h.GuildID && p.ChannelID() != nil && *p.ChannelID() == h.ChannelID {
		h.track = event.Track
		h.isPlaying = true
		h.track.Info.Position = 0 // Reset position to 0 on track start
		h.broadcastUpdate()
	}
}

func (h *TrackerHandler) OnTrackEnd(p disgolink.Player, event lavalink.TrackEndEvent) {
	h.mutex.Lock()
	defer h.mutex.Unlock()

	/* we don't check for channel id because either
	the target channel has finished playing or
	the player is not in target channel initially */
	if p.GuildID() == h.GuildID {
		h.track = lavalink.Track{}
		h.isPlaying = false
		h.broadcastUpdate()
	}
}

func (h *TrackerHandler) OnPlayerUpdate(p disgolink.Player, event lavalink.PlayerUpdateMessage) {
	h.mutex.Lock()
	defer h.mutex.Unlock()

	if p.GuildID() == h.GuildID && event.State.Connected && p.ChannelID() != nil && *p.ChannelID() == h.ChannelID {
		if h.isPlaying {
			h.isPaused = p.Paused()                      /* whether player is paused */
			h.track.Info.Position = event.State.Position /* update player position */
			h.broadcastUpdate()
		}
	}
}
