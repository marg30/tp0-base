package common

import (
	"bytes"
	"encoding/binary"
)

type ServerResponse struct {
	BatchID   [4]byte
	BatchSize [4]byte
}

// DeserializeResponse Deserialize the response from a byte slice
func DeserializeResponse(data []byte) (*ServerResponse, error) {
	response := &ServerResponse{}
	buf := bytes.NewReader(data)

	if _, err := buf.Read(response.BatchID[:]); err != nil {
		return nil, err
	}

	if _, err := buf.Read(response.BatchSize[:]); err != nil {
		return nil, err
	}

	return response, nil
}

func (r *ServerResponse) AsIntegers() (int, int) {
	batchIDInt := binary.BigEndian.Uint32(r.BatchID[:])
	batchSizeInt := binary.BigEndian.Uint32(r.BatchSize[:])
	return int(batchIDInt), int(batchSizeInt)
}
