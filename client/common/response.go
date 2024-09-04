package common

import (
    "encoding/binary"
    "bytes"
)

type ServerResponse struct {
    Document        [8]byte
    NumberLength    uint8
    Number          []byte
}

// Serialize the response into a byte slice
func (r *ServerResponse) SerializeResponse() ([]byte, error) {
    var buf bytes.Buffer

    buf.Write(r.Document[:])
    // Write the NumberLength and Number fields
    buf.WriteByte(r.NumberLength)
    buf.Write(r.Number)

    return buf.Bytes(), nil
}

// Deserialize the response from a byte slice
func DeserializeResponse(data []byte) (*ServerResponse, error) {
    response := &ServerResponse{}
    buf := bytes.NewReader(data)

    // Read the Document field (fixed size)
    if _, err := buf.Read(response.Document[:]); err != nil {
        return nil, err
    }

    // Read the NumberLength and Number fields
    if err := binary.Read(buf, binary.BigEndian, &response.NumberLength); err != nil {
        return nil, err
    }
    response.Number = make([]byte, response.NumberLength)
    if _, err := buf.Read(response.Number); err != nil {
        return nil, err
    }

    return response, nil
}

func (r *ServerResponse) AsIntegers() (uint64, uint64) {
    documentInt := binary.BigEndian.Uint64(r.Document[:])
    var numberInt uint64
    // Convert the Number to an integer based on its length
    switch len(r.Number) {
    case 4:
        numberInt = uint64(binary.BigEndian.Uint32(r.Number))
    case 8:
        numberInt = binary.BigEndian.Uint64(r.Number)
    default:
        return 0, 0
    }
    return documentInt, numberInt
}