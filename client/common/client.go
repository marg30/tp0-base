package common

import (
	"bufio"
	"context"
	"encoding/binary"
	"fmt"
	"net"
	"os"
	"strings"
	"time"

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
func (c *Client) StartClientLoop(ctx context.Context, cancel context.CancelFunc) {
	fileName := fmt.Sprintf("agency-%s.csv", c.config.ID)
	file, err := os.Open(fileName)
	if err != nil {
		log.Errorf(
			"Error opening file: %v",
			err,
		)
		return
	}
	defer func(file *os.File) {
		err := file.Close()
		if err != nil {
			log.Errorf(
				"Error closing file: %v",
				err,
			)
			return
		}
	}(file)

	scanner := bufio.NewScanner(file)
	var batch []Packet
	batchID := 0

	// Leer y procesar el archivo CSV mientras se envían los batches
	for scanner.Scan() {
		line := scanner.Text()
		fields := strings.Split(line, ",")

		if len(fields) != 5 {
			log.Warningf("Invalid line format: %v", line)
			continue
		}

		packet := NewPacket(fields[0], fields[1], fields[2], fields[3], fields[4])
		batch = append(batch, packet)

	// Si se completa el tamaño del batch, enviarlo
		if len(batch) == c.config.BatchAmount {
		c.sendAndResetBatch(&batch, batchID)
		batchID++
		}
	}

	// Enviar el último batch si no está vacío
	if len(batch) > 0 {
		c.sendAndResetBatch(&batch, batchID)
	}

		if err := scanner.Err(); err != nil {
			log.Errorf("Error reading file: %v", err)
		}

	// Notificar que se ha completado el procesamiento
	cancel()
		}

// sendAndResetBatch Envía un batch y resetea el slice
func (c *Client) sendAndResetBatch(batch *[]Packet, batchID int) {
	err := c.createClientSocket()
		if err != nil {
			log.Errorf("Error creating client socket: %v", err)
			return
		}
	defer c.conn.Close()

	protocol, err := NewProtocol(c.conn, c.config.ID)
	if err != nil {
		log.Criticalf("action: serialize_data | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}

	c.sendBatch(batchID, *batch, protocol)

	// Limpiar el batch
	*batch = nil
}

func (c *Client) sendBatch(batchID int, batch []Packet, protocol *Protocol) {
	log.Debugf("Sending batch ID: %v", batchID)
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
	binary.BigEndian.PutUint32(batchLength, uint32(len(batch)))
	batchIDBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(batchIDBytes, uint32(batchID))
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
	if err != nil {
		log.Errorf(
			"action: deser | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}

	batchID, batchSize := responsePacket.AsIntegers()
	log.Infof("action: batch_sent | result: success | batch_id: %v | cantidad: %v", batchID, batchSize)
}

// Shutdown handles the cleanup of resources
func (c *Client) Shutdown() {
	log.Infof("action: shutdown_client | result: in_progress | client_id: %v", c.config.ID)
	time.Sleep(2 * time.Second)
	log.Infof("action: shutdown_client | result: success | client_id: %v", c.config.ID)
}
