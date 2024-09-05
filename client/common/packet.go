package common

import (
	"bytes"
	"encoding/binary"
	"strconv"
)

type BetPacket struct {
	NameLength     uint8
	Name           []byte
	LastNameLength uint8
	LastName       []byte
	Document       [8]byte
	BirthDate      [10]byte
	Number         [4]byte
}

func NewPacket(name string, lastName string, document string, birthDate string, number string) BetPacket {
	packet := BetPacket{}

	packet.NameLength = uint8(len(name))
	packet.Name = []byte(name)

	packet.LastNameLength = uint8(len(lastName))
	packet.LastName = []byte(lastName)

	docInt, _ := strconv.ParseUint(document, 10, 64)
	binary.BigEndian.PutUint64(packet.Document[:], docInt)

	copy(packet.BirthDate[:], birthDate)

	numInt, _ := strconv.ParseUint(number, 10, 32)
	binary.BigEndian.PutUint32(packet.Number[:], uint32(numInt))

	return packet
}

// Serialize the packet into a byte slice
func (p *BetPacket) Serialize() ([]byte, error) {
	var buf bytes.Buffer

	// Write the NameLength and Name fields
	buf.WriteByte(p.NameLength)
	buf.Write(p.Name)

	// Write the LastNameLength and LastName fields
	buf.WriteByte(p.LastNameLength)
	buf.Write(p.LastName)

	// Write the Document field (fixed size)
	buf.Write(p.Document[:])

	// Write the BirthDate field (fixed size)
	buf.Write(p.BirthDate[:])

	buf.Write(p.Number[:])

	return buf.Bytes(), nil
}

type FinishedNotification struct {
	ClientID uint8
}

func NewNotification(id string) FinishedNotification {
	clientID, _ := strconv.ParseUint(id, 10, 8)
	notification := FinishedNotification{
		ClientID: uint8(clientID),
	}
	return notification
}

func (p *FinishedNotification) Serialize() ([]byte, error) {
	var buf bytes.Buffer

	// Write the NameLength and Name fields
	buf.WriteByte(p.ClientID)
	return buf.Bytes(), nil
}

type WinnerResponse struct {
	Amount uint32
}

func DeserializeWinnerResponse(data []byte) (*WinnerResponse, error) {
	response := &WinnerResponse{}
	buf := bytes.NewReader(data)
	if err := binary.Read(buf, binary.BigEndian, &response.Amount); err != nil {
		return nil, err
	}
	return response, nil
}
