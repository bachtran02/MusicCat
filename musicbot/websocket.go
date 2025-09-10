package musicbot

import (
	"log/slog"
	"net/http"
	"slices"

	"github.com/gorilla/websocket"
)

type WsServer struct {
	clients        map[*Connection]bool
	Broadcast      chan []byte
	register       chan *Connection
	unregister     chan *Connection
	allowedOrigins []string
	upgrader       websocket.Upgrader
}

func NewWsServer(allowedOrigins []string) *WsServer {
	s := &WsServer{
		Broadcast:      make(chan []byte),
		register:       make(chan *Connection),
		unregister:     make(chan *Connection),
		clients:        make(map[*Connection]bool),
		allowedOrigins: allowedOrigins,
	}

	s.upgrader = websocket.Upgrader{
		ReadBufferSize:  1024,
		WriteBufferSize: 1024,
		CheckOrigin: func(r *http.Request) bool {
			if len(s.allowedOrigins) == 0 {
				return true
			}
			origin := r.Header.Get("Origin")
			return slices.Contains(s.allowedOrigins, origin)
		},
	}
	return s
}

func (s *WsServer) Run() {
	for {
		select {
		case connection := <-s.register:
			/* register client */
			s.clients[connection] = true
		case connection := <-s.unregister:
			/* unregister client */
			if _, ok := s.clients[connection]; ok {
				/* If the connection exists in the map,
				remove it and close the send channel. */
				delete(s.clients, connection)
				close(connection.send)
			}
		case message := <-s.Broadcast:
			/* receiving messages from application */
			for connection := range s.clients {
				select {
				case connection.send <- message: // send message to clients
				default:
					close(connection.send)
					delete(s.clients, connection)
				}
			}
		}
	}
}

// an intermediary between the websocket connection and the server.
type Connection struct {
	server *WsServer
	conn   *websocket.Conn /* websocket connection. */
	send   chan []byte     /* buffered channel of outbound messages */
}

// writePump pumps messages from the server to the websocket connection.
func (c *Connection) writePump() {
	defer func() {
		c.server.unregister <- c
		c.conn.Close()
	}()
	for {
		message, ok := <-c.send
		if !ok {
			// The server closed the channel.
			c.conn.WriteMessage(websocket.CloseMessage, []byte{})
			return
		}
		if err := c.conn.WriteMessage(websocket.TextMessage, message); err != nil {
			return
		}
	}
}

// ServeWs handles websocket requests from the peer.
func ServeWs(server *WsServer, w http.ResponseWriter, r *http.Request) {
	conn, err := server.upgrader.Upgrade(w, r, nil)
	if err != nil {
		slog.Error("failed to upgrade http connection to websocket", slog.Any("err", err))
		return
	}
	connection := &Connection{server: server, conn: conn, send: make(chan []byte, 256)}
	server.register <- connection

	/* Allow collection of memory referenced by the caller
	by doing all work in new goroutines. */
	go connection.writePump()
}
