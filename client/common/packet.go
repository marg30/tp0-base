package common

import (
    "encoding/binary"
    "bytes"
    "os"
    "fmt"
    "strconv"
)

type Packet struct {
    NameLength      uint8
    Name            []byte
    LastNameLength  uint8
    LastName        []byte
    Document        [8]byte
    BirthDate       [10]byte
    Number          [4]byte
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

// Deserialize the packet from a byte slice
func Deserialize(data []byte) (*Packet, error) {
    packet := &Packet{}
    buf := bytes.NewReader(data)
    // Read the NameLength and Name fields
    if err := binary.Read(buf, binary.BigEndian, &packet.NameLength); err != nil {
        return nil, err
    }
    packet.Name = make([]byte, packet.NameLength)
    if _, err := buf.Read(packet.Name); err != nil {
        return nil, err
    }

    // Read the LastNameLength and LastName fields
    if err := binary.Read(buf, binary.BigEndian, &packet.LastNameLength); err != nil {
        return nil, err
    }
    packet.LastName = make([]byte, packet.LastNameLength)
    if _, err := buf.Read(packet.LastName); err != nil {
        return nil, err
    }

    // Read the Document field (fixed size)
    if _, err := buf.Read(packet.Document[:]); err != nil {
        return nil, err
    }

    // Read the BirthDate field (fixed size)
    if _, err := buf.Read(packet.BirthDate[:]); err != nil {
        return nil, err
    }

    if _, err := buf.Read(packet.Number[:]); err != nil {
        return nil, err
    }

    return packet, nil
}

func getEnvAsInt(name string, defaultValue int) int {
	value, exists := os.LookupEnv(name)
	if !exists {
		return defaultValue
	}

	intValue, err := strconv.Atoi(value)
	if err != nil {
		fmt.Printf("Warning: could not convert %s to int: %v\n", name, err)
		return defaultValue
	}
	return intValue
}

func CreatePacketFromEnv() Packet {
    name := os.Getenv("NOMBRE")
    last_name := os.Getenv("APELLIDO")
    document := os.Getenv("DOCUMENTO")
    birthDate := os.Getenv("NACIMIENTO")
    number := os.Getenv("NUMERO")

	return NewPacket(name, last_name, document, birthDate, number)
}

