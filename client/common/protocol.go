package common

import (
	"bytes"
	"encoding/binary"
	"net"
	"strconv"
)

// Protocol Struct to handle communication protocol
type Protocol struct {
	conn net.Conn
	ID byte
}

// NewProtocol Initializes a new Protocol instance
func NewProtocol(conn net.Conn, ID string) (*Protocol, error) {
	idInt, err := strconv.Atoi(ID)
	if err != nil {
		return nil, err
	}
	return &Protocol{conn: conn, ID: byte(idInt)}, nil
}

// SendMessage Sends a message with a header containing the length of the data
func (p *Protocol) SendMessage(data []byte) error {
	allData := append([]byte{p.ID}, data...)
	log.Debugf("byte array: %v", allData)

	dataLength := uint32(len(allData))
	var lengthBuffer bytes.Buffer
	log.Debugf("length: %d", dataLength)

	err := binary.Write(&lengthBuffer, binary.BigEndian, dataLength)
	if err != nil {
		return err
	}

	if err := p.sendAll(lengthBuffer.Bytes()); err != nil {
		return err
	}

	return p.sendAll(allData)
}

// sendAll Ensures that all data is sent, handling short writes
func (p *Protocol) sendAll(data []byte) error {
	totalBytesSent := 0
	for totalBytesSent < len(data) {
		bytesSent, err := p.conn.Write(data[totalBytesSent:])
		if err != nil {
			return err
		}
		totalBytesSent += bytesSent
	}
	return nil
}

// ReceiveMessage Receives a message by first reading the length header and then the data
func (p *Protocol) ReceiveMessage() ([]byte, error) {
	lengthBuffer := make([]byte, 4)
	if err := p.readAll(lengthBuffer); err != nil {
		return nil, err
	}

	var dataLength uint32
	lengthReader := bytes.NewReader(lengthBuffer)
	err := binary.Read(lengthReader, binary.BigEndian, &dataLength)
	if err != nil {
		return nil, err
	}

	data := make([]byte, dataLength)
	if err := p.readAll(data); err != nil {
		return nil, err
	}

	return data, nil
}

// readAll Ensures that all data is read, handling short reads
func (p *Protocol) readAll(data []byte) error {
	totalBytesRead := 0
	for totalBytesRead < len(data) {
		bytesRead, err := p.conn.Read(data[totalBytesRead:])
		if err != nil {
			return err
		}
		totalBytesRead += bytesRead
	}
	return nil
}
