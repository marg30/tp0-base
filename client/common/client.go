package common

import (
	"net"
	"time"
	"fmt"
	"context"
	"bufio"
	"os"
	"encoding/binary"
	"strings"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	BatchAmount   int
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
func (c *Client) StartClientLoop(ctx context.Context) {
	select {
	case <-ctx.Done():
		log.Infof("Client loop stopped due to shutdown signal")
		return
	default:
		fileName := fmt.Sprintf("agency-%s.csv", c.config.ID)
		file, err := os.Open(fileName)
		if err != nil {
			log.Errorf(
				"Error opening file: %v", 
				err, 
			)
			return
		}
		defer file.Close()
	
		scanner := bufio.NewScanner(file)
		var batches [][]BetPacket
		var batch []BetPacket

		// Procesar el archivo y dividir en lotes
		for scanner.Scan() {
			line := scanner.Text()
			fields := strings.Split(line, ",")

			if len(fields) != 5 {
				log.Warningf("Invalid line format: %v", line)
				continue
			}

			packet := NewPacket(fields[0], fields[1], fields[2], fields[3], fields[4])
			batch = append(batch, packet)

			if len(batch) == c.config.BatchAmount {
				batches = append(batches, batch)
				batch = nil
			}
		}

		if err := scanner.Err(); err != nil {
			log.Errorf("Error reading file: %v", err)
		}

		// Añadir el último batch si tiene elementos
		if len(batch) > 0 {
			batches = append(batches, batch)
		}

		err = c.createClientSocket()
		if err != nil {
			log.Errorf("Error creating client socket: %v", err)
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

		// Enviar cada batch por separado, creando una nueva conexión para cada uno
		for batchID, batch := range batches {
			log.Debugf("Sending batch")
			c.sendBatch(batchID, batch, protocol)
		}
		finishNotification := NewNotification(c.config.ID)
		encodedNotification, _ := finishNotification.Serialize()
		protocol.SendMessage(encodedNotification)
		responseData, err := protocol.ReceiveMessage()
		if err != nil {
			log.Errorf(
				"action: receive_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}
		responsePacket, err := DeserializeWinnerResponse(responseData)
		log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %v", responsePacket.Amount)
		c.conn.Close()
	}
}

func (c *Client) sendBatch(batchID int, batch []BetPacket, protocol *Protocol) {
	log.Debugf("Batch ID: %v", batchID)
	var allData []byte
	for _, packet := range batch {
		data, err := packet.Serialize()
		if err != nil {
			log.Criticalf(
				"action: serialize_data | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}
		allData = append(allData, data...)
	}

	batchLength := make([]byte, 4)
	binary.BigEndian.PutUint32(batchLength,	uint32(len(batch)))
	batchIDBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(batchIDBytes, uint32(batchID))
	log.Debugf("byte length: %v", batchLength)
	allData = append(batchLength, allData...)
	allData = append(batchIDBytes, allData...)

	if err := protocol.SendMessage(allData); err != nil {
		log.Criticalf(
			"action: send_message | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return
	}

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
	batchID, batchSize := responsePacket.AsIntegers()
	log.Infof("action: batch_sent | result: success | batch_id: %v | cantidad: %v", batchID, batchSize)
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