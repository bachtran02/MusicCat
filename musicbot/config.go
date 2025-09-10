package musicbot

import (
	"fmt"
	"os"

	"github.com/disgoorg/snowflake/v2"
	"gopkg.in/yaml.v3"
)

func ReadConfig(path string) (Config, error) {
	file, err := os.Open(path)
	if err != nil {
		return Config{}, fmt.Errorf("failed to open config: %w", err)
	}
	defer file.Close()

	cfg := Config{
		MusicTracker: TrackerConfig{
			Enabled: false,
		},
		Log: LogConfig{
			Level:  "info",
			Format: "text",
		},
	}
	if err = yaml.NewDecoder(file).Decode(&cfg); err != nil {
		return Config{}, fmt.Errorf("failed to decode config: %w", err)
	}
	return cfg, nil
}

type Config struct {
	Bot          BotConfig     `yaml:"bot"`
	Nodes        []NodeConfig  `yaml:"nodes"`
	MusicTracker TrackerConfig `yaml:"music_tracker"`
	DB           DBConfig      `yaml:"database"`
	Log          LogConfig     `yaml:"log"`
}

type BotConfig struct {
	Token string `yaml:"token"`
}

type LogConfig struct {
	Level     string `yaml:"level"`
	Format    string `yaml:"format"`
	FilePath  string `yaml:"file_path"`
	AddSource bool   `yaml:"add_source"`
	Env       string `yaml:"env"`
}

type NodeConfig struct {
	Name      string `yaml:"name"`
	Address   string `yaml:"address"`
	Password  string `yaml:"password"`
	Secure    bool   `yaml:"secure"`
	SessionID string `yaml:"session_id"`
}

type TrackerConfig struct {
	Enabled        bool         `yaml:"enabled"`
	ChannelID      snowflake.ID `yaml:"channel_id"`
	GuildID        snowflake.ID `yaml:"guild_id"`
	HostAddress    string       `yaml:"host_address"`
	HttpPath       string       `yaml:"http_path"`
	WebsocketPath  string       `yaml:"websocket_path"`
	AllowedOrigins []string     `yaml:"allowed_origins"`
}

type DBConfig struct {
	Host     string `yaml:"host"`
	Port     int    `yaml:"port"`
	Username string `yaml:"username"`
	Password string `yaml:"password"`
	Database string `yaml:"database"`
}
