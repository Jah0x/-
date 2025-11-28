package config

import (
	"errors"
	"os"
	"strconv"
	"strings"
	"time"

	"gopkg.in/yaml.v3"
)

type Config struct {
	ListenAddr           string
	TLSCertPath          string
	TLSKeyPath           string
	BackendBaseURL       string
	BackendSecret        string
	BackendTimeout       time.Duration
	UpstreamMode         string
	LogLevel             string
	LogFormat            string
	MetricsEnabled       bool
	MetricsPath          string
	MaxStreamsPerSession int
}

type fileConfig struct {
	ListenAddr           string        `yaml:"listen_addr"`
	TLSCertPath          string        `yaml:"tls_cert_path"`
	TLSKeyPath           string        `yaml:"tls_key_path"`
	BackendBaseURL       string        `yaml:"backend_base_url"`
	BackendSecret        string        `yaml:"backend_secret"`
	BackendTimeout       time.Duration `yaml:"backend_timeout"`
	UpstreamMode         string        `yaml:"upstream_mode"`
	LogLevel             string        `yaml:"log_level"`
	LogFormat            string        `yaml:"log_format"`
	MetricsEnabled       *bool         `yaml:"metrics_enabled"`
	MetricsPath          string        `yaml:"metrics_path"`
	MaxStreamsPerSession int           `yaml:"max_streams_per_session"`
}

func defaultConfig() Config {
	return Config{
		ListenAddr:           ":8443",
		BackendTimeout:       5 * time.Second,
		UpstreamMode:         "fake",
		LogLevel:             "info",
		LogFormat:            "json",
		MetricsEnabled:       true,
		MetricsPath:          "/metrics",
		MaxStreamsPerSession: 8,
	}
}

func Load() (Config, error) {
	cfg := defaultConfig()
	if path := strings.TrimSpace(os.Getenv("GATEWAY_CONFIG_PATH")); path != "" {
		loaded, err := loadFromFile(path)
		if err != nil {
			return cfg, err
		}
		mergeFileConfig(&cfg, loaded)
	}
	applyEnv(&cfg)
	if cfg.ListenAddr == "" || cfg.TLSCertPath == "" || cfg.TLSKeyPath == "" || cfg.BackendBaseURL == "" {
		return cfg, errors.New("missing required configuration")
	}
	return cfg, nil
}

func loadFromFile(path string) (fileConfig, error) {
	var fc fileConfig
	content, err := os.ReadFile(path)
	if err != nil {
		return fc, err
	}
	if strings.HasSuffix(strings.ToLower(path), ".json") {
		decoder := yaml.NewDecoder(strings.NewReader(string(content)))
		decoder.KnownFields(true)
		if err := decoder.Decode(&fc); err != nil {
			return fc, err
		}
		return fc, nil
	}
	if err := yaml.Unmarshal(content, &fc); err != nil {
		return fc, err
	}
	return fc, nil
}

func mergeFileConfig(cfg *Config, fc fileConfig) {
	if fc.ListenAddr != "" {
		cfg.ListenAddr = fc.ListenAddr
	}
	if fc.TLSCertPath != "" {
		cfg.TLSCertPath = fc.TLSCertPath
	}
	if fc.TLSKeyPath != "" {
		cfg.TLSKeyPath = fc.TLSKeyPath
	}
	if fc.BackendBaseURL != "" {
		cfg.BackendBaseURL = fc.BackendBaseURL
	}
	if fc.BackendSecret != "" {
		cfg.BackendSecret = fc.BackendSecret
	}
	if fc.BackendTimeout != 0 {
		cfg.BackendTimeout = fc.BackendTimeout
	}
	if fc.UpstreamMode != "" {
		cfg.UpstreamMode = fc.UpstreamMode
	}
	if fc.LogLevel != "" {
		cfg.LogLevel = fc.LogLevel
	}
	if fc.LogFormat != "" {
		cfg.LogFormat = fc.LogFormat
	}
	if fc.MetricsEnabled != nil {
		cfg.MetricsEnabled = *fc.MetricsEnabled
	}
	if fc.MetricsPath != "" {
		cfg.MetricsPath = fc.MetricsPath
	}
	if fc.MaxStreamsPerSession > 0 {
		cfg.MaxStreamsPerSession = fc.MaxStreamsPerSession
	}
}

func applyEnv(cfg *Config) {
	if value := strings.TrimSpace(os.Getenv("GATEWAY_LISTEN_ADDR")); value != "" {
		cfg.ListenAddr = value
	}
	if value := strings.TrimSpace(os.Getenv("GATEWAY_TLS_CERT_PATH")); value != "" {
		cfg.TLSCertPath = value
	}
	if value := strings.TrimSpace(os.Getenv("GATEWAY_TLS_KEY_PATH")); value != "" {
		cfg.TLSKeyPath = value
	}
	if value := strings.TrimSpace(os.Getenv("BACKEND_BASE_URL")); value != "" {
		cfg.BackendBaseURL = value
	}
	if value := strings.TrimSpace(os.Getenv("BACKEND_GATEWAY_SECRET")); value != "" {
		cfg.BackendSecret = value
	}
	if value := strings.TrimSpace(os.Getenv("BACKEND_TIMEOUT")); value != "" {
		if duration, err := time.ParseDuration(value); err == nil {
			cfg.BackendTimeout = duration
		}
	}
	if value := strings.TrimSpace(os.Getenv("GATEWAY_UPSTREAM_MODE")); value != "" {
		cfg.UpstreamMode = strings.ToLower(value)
	}
	if value := strings.TrimSpace(os.Getenv("GATEWAY_LOG_LEVEL")); value != "" {
		cfg.LogLevel = strings.ToLower(value)
	}
	if value := strings.TrimSpace(os.Getenv("GATEWAY_LOG_FORMAT")); value != "" {
		cfg.LogFormat = strings.ToLower(value)
	}
	if value := strings.TrimSpace(os.Getenv("GATEWAY_METRICS_ENABLED")); value != "" {
		if parsed, err := strconv.ParseBool(value); err == nil {
			cfg.MetricsEnabled = parsed
		}
	}
	if value := strings.TrimSpace(os.Getenv("GATEWAY_METRICS_PATH")); value != "" {
		cfg.MetricsPath = value
	}
	if value := strings.TrimSpace(os.Getenv("GATEWAY_MAX_STREAMS")); value != "" {
		if parsed, err := strconv.Atoi(value); err == nil && parsed > 0 {
			cfg.MaxStreamsPerSession = parsed
		}
	}
}
