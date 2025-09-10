package musicbot

import (
	"context"
	"fmt"
	"log/slog"
	"net/http"
)

type HttpServer struct {
	server *http.Server
}

func NewTrackerServer(wsServer *WsServer, trackerHandler func(http.ResponseWriter, *http.Request),
	host string, http_path string, ws_path string) *HttpServer {
	mux := http.NewServeMux()
	/* serve tracker handler */
	mux.HandleFunc(fmt.Sprintf("/%s", http_path), trackerHandler)
	/* serve websocket handler */
	mux.HandleFunc(fmt.Sprintf("/%s", ws_path), func(w http.ResponseWriter, r *http.Request) {
		ServeWs(wsServer, w, r)
	})

	s := &HttpServer{
		server: &http.Server{
			Addr:    host,
			Handler: mux,
		},
	}
	return s
}

func (s *HttpServer) Start() {
	if err := s.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		slog.Error("failed to start http server", slog.Any("err", err))
	}
}

func (s *HttpServer) Close(ctx context.Context) {
	if err := s.server.Shutdown(ctx); err != nil {
		slog.Error("failed to shut down http server", slog.Any("err", err))
	}
}
