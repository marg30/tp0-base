package common

import (
	"bytes"
	"encoding/binary"
	"strconv"
)

type Packet struct {
	NameLength     uint8
	Name           []byte
	LastNameLength uint8
	LastName       []byte
	Document       [8]byte
	BirthDate      [10]byte
	Number         [4]byte
}

func NewPacket(name string, lastName string, document string, birthDate string, number string) Packet {
	packet := Packet{}

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
func (p *Packet) Serialize() ([]byte, error) {
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
