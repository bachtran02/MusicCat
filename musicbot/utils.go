package musicbot

import (
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/disgoorg/disgo/handler"
	"github.com/disgoorg/disgolink/v3/lavalink"
	"github.com/disgoorg/lavasrc-plugin"
)

const deleteAfter = 30

const (
	RESUME_PLAYER_EMOJI_ID   int = 1187705966263812218
	PAUSE_PLAYER_EMOJI_ID    int = 1187705962358902806
	STOP_PLAYER_EMOJI_ID     int = 1187705975638081557
	PLAYER_PREVIOUS_EMOJI_ID int = 1187705971070488627
	PLAYER_NEXT_EMOJI_ID     int = 1187705968331591710

	LOOP_OFF_EMOJI_ID     int = 1189020553353371678
	LOOP_TRACK_EMOJI_ID   int = 1189020551340114032
	LOOP_QUEUE_EMOJI_ID   int = 1189020548525735956
	SHUFFLE_OFF_EMOJI_ID  int = 1189022239354531890
	SHUFFLE_ON_EMOJI_ID   int = 1189022235621605498
	RADIO_BUTTON_EMOJI_ID int = 1187818871072247858
)

var (
	resumePlayerEmoji string = "<:mc_resume:" + strconv.Itoa(RESUME_PLAYER_EMOJI_ID) + ">"
	pausePlayerEmoji  string = "<:mc_pause:" + strconv.Itoa(PAUSE_PLAYER_EMOJI_ID) + ">"
)

func AutoRemove(e *handler.CommandEvent) {
	time.AfterFunc(deleteAfter*time.Second, func() {
		if err := e.DeleteInteractionResponse(); err != nil {
			LogDeleteError(err, e.GuildID().String(), e.Channel().ID().String(), "")
		}
	})
}

func Trim(s string, length int) string {
	r := []rune(s)
	if len(r) > length {
		return string(r[:length-1]) + "…"
	}
	return s
}

func FormatTrack(track lavalink.Track) string {

	var lavasrcInfo lavasrc.TrackInfo
	_ = track.PluginInfo.Unmarshal(&lavasrcInfo)

	return ""
}

func FormatTime(d lavalink.Duration) string {

	if d.Hours() < 1 {
		return fmt.Sprintf("%02d:%02d", d.MinutesPart(), d.SecondsPart())
	} else if d.Days() < 1 {
		return fmt.Sprintf("%02d:%02d:%02d", d.HoursPart(), d.MinutesPart(), d.SecondsPart())
	} else {
		return fmt.Sprintf("%02d:%02d:%02d:%02d", d.Days(), d.HoursPart(), d.MinutesPart(), d.SecondsPart())
	}
}

func PlayerBar(paused bool, track lavalink.Track, position lavalink.Duration) string {

	var (
		PlayPause string
		Playtime  string
		Bar       string
	)

	if paused {
		PlayPause = resumePlayerEmoji
	} else {
		PlayPause = pausePlayerEmoji
	}

	if track.Info.IsStream {
		Playtime = "LIVE"
		Bar = ProgressBar(0.99)
	} else {
		Playtime = fmt.Sprintf("`%s | %s`", FormatTime(position), FormatTime(track.Info.Length))
		Bar = ProgressBar(float32(position) / float32(track.Info.Length))
	}
	return fmt.Sprintf("%s %s `%s`", PlayPause, Bar, Playtime)
}

func ProgressBar(percent float32) string {

	bar := make([]rune, 12)

	for i := range bar {
		if i == int(percent*12) {
			bar[i] = '🔘'
		} else {
			bar[i] = '▬'
		}
	}
	return string(bar)
}

func ParseTime(timeStr string) (int, int, int, error) {
	// Split the time string by ":"
	parts := strings.Split(timeStr, ":")

	var hours, minutes, seconds int
	var err error

	// Handle "HH:MM:SS" format
	if len(parts) == 3 {
		hours, err = strconv.Atoi(parts[0])
		if err != nil {
			return 0, 0, 0, err
		}
		minutes, err = strconv.Atoi(parts[1])
		if err != nil {
			return 0, 0, 0, err
		}
		seconds, err = strconv.Atoi(parts[2])
		if err != nil {
			return 0, 0, 0, err
		}
	} else if len(parts) == 2 { // Handle "MM:SS" format
		minutes, err = strconv.Atoi(parts[0])
		if err != nil {
			return 0, 0, 0, err
		}
		seconds, err = strconv.Atoi(parts[1])
		if err != nil {
			return 0, 0, 0, err
		}
	} else { // Invalid format
		return 0, 0, 0, fmt.Errorf("invalid time format")
	}

	// Normalize seconds and minutes
	if seconds >= 60 {
		minutes += seconds / 60
		seconds = seconds % 60
	}
	if minutes >= 60 {
		hours += minutes / 60
		minutes = minutes % 60
	}

	return hours, minutes, seconds, nil
}
