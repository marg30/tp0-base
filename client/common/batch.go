package common

import (
	"encoding/binary"
	"fmt"
)

// Batch encapsulates a collection of BetPackets
type Batch struct {
	ID     int
	Packets []BetPacket
}

// NewBatch creates a new batch with an ID and a set of packets
func NewBatch(id int, packets []BetPacket) *Batch {
	return &Batch{
		ID:     id,
		Packets: packets,
	}
}

// Serialize serializes the entire batch into a byte slice
func (b *Batch) Serialize() ([]byte, error) {
	var allData []byte

	for _, packet := range b.Packets {
		data, err := packet.Serialize()
		if err != nil {
			return nil, fmt.Errorf("error serializing packet: %w", err)
		}
		allData = append(allData, data...)
	}

	// Serialize batch length and ID
	batchLength := make([]byte, 4)
	binary.BigEndian.PutUint32(batchLength, uint32(len(b.Packets)))

	batchIDBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(batchIDBytes, uint32(b.ID))

	// Append length and ID to serialized data
	allData = append(batchLength, allData...)
	allData = append(batchIDBytes, allData...)

	return allData, nil
}
