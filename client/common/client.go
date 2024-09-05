package common

import (
	"net"
	"time"
	"context"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates the client's logic
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(ctx context.Context, cancel context.CancelFunc) {
	select {
	case <-ctx.Done():
		log.Infof("Client loop stopped due to shutdown signal")
		return
	default:
		// Create the connection the server in every loop iteration. Send an
		err := c.createClientSocket()
		if err != nil {
			return
		}

		protocol, err := NewProtocol(c.conn, c.config.ID)
		if err != nil {
			log.Criticalf(
				"action: serialize_data | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}
		packet := CreatePacketFromEnv()

		// Serialize the packet
		data, err := packet.Serialize()
		if err != nil {
			log.Criticalf(
				"action: serialize_data | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		// Send the data using the protocol
		if err := protocol.SendMessage(data); err != nil {
			log.Criticalf(
				"action: send_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		// Receive and process the response
		responseData, err := protocol.ReceiveMessage()
		if err != nil {
			log.Errorf(
				"action: receive_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}
		responsePacket, err := DeserializeResponse(responseData)
		document, number := responsePacket.AsIntegers()

		log.Infof("action: apuesta_enviada | result: success | dni: %v | numero: %v",
		document, number,
		)

		c.conn.Close()
		cancel()
	}
}

// Shutdown handles the cleanup of resources
func (c *Client) Shutdown() {
	log.Infof("action: shutdown_client | result: in_progress | client_id: %v", c.config.ID)

	time.Sleep(2 * time.Second)

	if c.conn != nil {
		c.conn.Close()
	}

	log.Infof("action: shutdown_client | result: success | client_id: %v", c.config.ID)
}