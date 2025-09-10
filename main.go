package main

import (
	"MusicCatGo/commands"
	"MusicCatGo/handlers"
	"MusicCatGo/musicbot"
	"io"
	"path/filepath"
	"strconv"
	"time"

	"context"
	_ "embed"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/disgoorg/disgo"
	"github.com/disgoorg/disgo/bot"
	"github.com/disgoorg/disgo/cache"
	"github.com/disgoorg/disgo/discord"
	"github.com/disgoorg/disgo/gateway"
	"github.com/disgoorg/disgo/handler"
	"github.com/disgoorg/disgo/handler/middleware"
	"github.com/disgoorg/disgolink/v3/disgolink"
)

//go:embed db/schema.sql
var DBschema string

func setupLogger(cfg musicbot.LogConfig) {
	var level slog.Level
	switch cfg.Level {
	case "debug":
		level = slog.LevelDebug
	case "info":
		level = slog.LevelInfo
	case "warn":
		level = slog.LevelWarn
	case "error":
		level = slog.LevelError
	default:
		level = slog.LevelInfo
	}

	opts := &slog.HandlerOptions{
		Level:     level,
		AddSource: cfg.AddSource,
		ReplaceAttr: func(_ []string, a slog.Attr) slog.Attr {
			if a.Key == slog.TimeKey {
				/* formatting time to RFC3339 standard */
				t := a.Value.Time()
				a.Value = slog.StringValue(t.UTC().Format(time.RFC3339))
			}
			if a.Key == slog.SourceKey {
				if src, ok := a.Value.Any().(*slog.Source); ok {
					/* keep only the file name + line */
					src.File = filepath.Base(src.File)
					a.Value = slog.AnyValue(src)
				}
			}
			return a
		},
	}

	var (
		handler slog.Handler
		w       io.Writer = os.Stdout
	)

	if cfg.Env == "dev" {
		/* dev log text to stdout */
		handler = slog.NewTextHandler(w, opts)
	} else {
		/* prod based on config & if file exists */
		var mw io.Writer = os.Stdout
		if cfg.FilePath != "" {
			if f, err := os.OpenFile(cfg.FilePath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644); err == nil {
				mw = io.MultiWriter(os.Stdout, f)
			} else {
				slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelWarn})).
					Error("failed to open log file; using stdout only", "path", cfg.FilePath, "err", err)
			}
		}
		if cfg.Format == "json" {
			handler = slog.NewJSONHandler(mw, opts)
		} else {
			handler = slog.NewTextHandler(mw, opts)
		}
	}

	slog.SetDefault(slog.New(handler))

	/* logging startup info */
	slog.Info("logger initialized")
	slog.Info("startup",
		"env", cfg.Env,
		"pid", strconv.Itoa(os.Getpid()),
	)
}

func main() {

	cfg, err := musicbot.ReadConfig("config.yml")
	if err != nil {
		slog.Error("failed to read config file", slog.Any("err", err))
		os.Exit(-1)
	}
	/* setting up logger */
	setupLogger(cfg.Log)
	slog.Info("starting MusicCat",
		"disgo", disgo.Version,
		"disgolink", disgolink.Version,
	)

	b := &musicbot.Bot{Cfg: cfg}
	cmds := &commands.Commands{Bot: b}

	r := handler.New()
	r.Use(func(next handler.Handler) handler.Handler {
		return func(e *handler.InteractionEvent) error {
			if i, ok := any(e.Interaction).(discord.ApplicationCommandInteraction); ok {
				/* retrieve slash command interaction data */
				data := i.SlashCommandInteractionData()
				musicbot.LogCommand(data.CommandPath(), e.GuildID().String(), e.User().ID.String())
			}
			return next(e)
		}
	})
	r.Use(middleware.GoErr(func(e *handler.InteractionEvent, err error) {
		/* type-assert InteractionEvent to ApplicationCommandInteraction */
		if i, ok := any(e.Interaction).(discord.ApplicationCommandInteraction); ok {
			/* retrieve slash command interaction data */
			data := i.SlashCommandInteractionData()
			musicbot.LogCommandError(err, data.CommandPath(), e.GuildID().String(), e.User().ID.String())
		}
	}))
	r.Route("/bot", func(r handler.Router) {
		r.SlashCommand("/join", cmds.Connect)
		r.SlashCommand("/leave", cmds.Disconnect)
		r.SlashCommand("/ping", cmds.Ping)
	})
	r.Route("/music", func(r handler.Router) {
		r.SlashCommand("/loop", cmds.Loop)
		r.SlashCommand("/now", cmds.Now)
		r.SlashCommand("/pause", cmds.Pause)
		r.SlashCommand("/play", cmds.Play)
		r.SlashCommand("/playlist", cmds.PlayPlaylist)
		r.Autocomplete("/playlist", cmds.PlaylistAutocomplete)
		r.SlashCommand("/queue", cmds.Queue)
		r.SlashCommand("/remove", cmds.RemoveQueueTrack)
		r.Autocomplete("/remove", cmds.RemoveQueueTrackAutocomplete)
		r.SlashCommand("/resume", cmds.Resume)
		r.SlashCommand("/search", cmds.Play)
		r.Autocomplete("/search", cmds.SearchAutocomplete)
		r.SlashCommand("/seek", cmds.Seek)
		r.SlashCommand("/shuffle", cmds.Shuffle)
		r.SlashCommand("/skip", cmds.Skip)
		r.SlashCommand("/stop", cmds.Stop)
	})
	r.Route("/list", func(r handler.Router) {
		r.SlashCommand("/add", cmds.AddPlaylistTrack)
		r.Autocomplete("/add", cmds.AddPlaylistTrackAutocomplete)
		r.SlashCommand("/create", cmds.CreatePlaylist)
		r.SlashCommand("/delete", cmds.DeletePlaylist)
		r.Autocomplete("/delete", cmds.PlaylistAutocomplete)
		r.SlashCommand("/list", cmds.ListPlaylists)
		r.SlashCommand("/remove", cmds.RemovePlaylistTrack)
		r.Autocomplete("/remove", cmds.RemovePlaylistTrackAutocomplete)
	})

	hdlr := &handlers.Handlers{Bot: b}

	b.Client, err = disgo.New(cfg.Bot.Token,
		bot.WithGatewayConfigOpts(
			gateway.WithIntents(
				gateway.IntentGuilds,
				gateway.IntentGuildVoiceStates,
			)),
		bot.WithCacheConfigOpts(
			cache.WithCaches(cache.FlagVoiceStates),
		),
		bot.WithEventListeners(r),
		bot.WithEventListenerFunc(hdlr.OnVoiceStateUpdate),
		bot.WithEventListenerFunc(hdlr.OnVoiceServerUpdate),
		bot.WithEventListenerFunc(hdlr.OnPlayerInteraction),
	)
	if err != nil {
		slog.Error("failed to create disgo client", slog.Any("error", err))
		return
	}

	if err = handler.SyncCommands(b.Client, commands.CommandCreates, nil); err != nil {
		slog.Error("failed to sync commands", slog.Any("error", err))
	}

	if b.Lavalink = disgolink.New(b.Client.ApplicationID(),
		disgolink.WithListenerFunc(hdlr.OnTrackStart),
		disgolink.WithListenerFunc(hdlr.OnTrackEnd),
		// disgolink.WithListenerFunc(hdlr.OnTrackException),
		// disgolink.WithListenerFunc(hdlr.OnTrackStuck),
	); err != nil {
		slog.Error("failed to create disgolink client", slog.Any("error", err))
		os.Exit(-1)
	}
	/* link player manager to disgolink client */
	b.PlayerManager = *musicbot.NewPlayerManager(b.Lavalink)

	b.Db, err = musicbot.NewDB(cfg.DB, DBschema)
	if err != nil {
		slog.Error("failed to connect to database", slog.Any("error", err))
		os.Exit(-1)
	}
	slog.Info("connected to database")
	defer b.Db.Close()

	if err = b.Start(); err != nil {
		slog.Error("failed to start bot", slog.Any("err", err))
		os.Exit(-1)
	}
	defer b.Client.Close(context.TODO())

	slog.Info("MusicCat is now running")

	if b.Cfg.MusicTracker.Enabled {
		/* enabling tracker server */
		wsServer := musicbot.NewWsServer(b.Cfg.MusicTracker.AllowedOrigins)
		go wsServer.Run()

		trackerHandler := handlers.TrackerHandler{
			ChannelID: b.Cfg.MusicTracker.ChannelID,
			GuildID:   b.Cfg.MusicTracker.GuildID,
			WsServer:  wsServer,
		}

		// run tracker server to serve current track
		trackerServer := musicbot.NewTrackerServer(
			wsServer,
			trackerHandler.ServeHTTP,
			b.Cfg.MusicTracker.HostAddress,
			b.Cfg.MusicTracker.HttpPath,
			b.Cfg.MusicTracker.WebsocketPath)

		go trackerServer.Start()
		defer trackerServer.Close(context.TODO())

		// register lavalink client listener
		b.Lavalink.AddListeners(
			disgolink.NewListenerFunc(trackerHandler.OnTrackStart),
			disgolink.NewListenerFunc(trackerHandler.OnTrackEnd),
			disgolink.NewListenerFunc(trackerHandler.OnPlayerUpdate),
		)
		slog.Info(
			"MusicCat music tracker is enabled",
			slog.String("http", fmt.Sprintf("%s/%s",
				b.Cfg.MusicTracker.HostAddress,
				b.Cfg.MusicTracker.HttpPath)),
			slog.String("ws", fmt.Sprintf("%s/%s",
				b.Cfg.MusicTracker.HostAddress,
				b.Cfg.MusicTracker.WebsocketPath)),
		)
	}

	s := make(chan os.Signal, 1)
	signal.Notify(s, syscall.SIGINT, syscall.SIGTERM, os.Interrupt)
	<-s
}
