package upstream

import (
	"context"
	"encoding/json"
	"time"

	"github.com/nats-io/nats.go"
)

type NATSStore struct {
	bucket nats.KeyValue
}

func NewNATSStore(conn *nats.Conn, bucket string, ttl time.Duration) (*NATSStore, error) {
	js, err := conn.JetStream()
	if err != nil {
		return nil, err
	}
	kv, err := js.KeyValue(bucket)
	if err == nats.ErrBucketNotFound {
		kv, err = js.CreateKeyValue(&nats.KeyValueConfig{Bucket: bucket, TTL: ttl})
	}
	if err != nil {
		return nil, err
	}
	return &NATSStore{bucket: kv}, nil
}

func (n *NATSStore) Save(ctx context.Context, sessionID string, node OutlineNodeConfig) error {
	payload, err := json.Marshal(node)
	if err != nil {
		return err
	}
	_, err = n.bucket.Put(sessionID, payload)
	return err
}

func (n *NATSStore) Load(ctx context.Context, sessionID string) (OutlineNodeConfig, bool, error) {
	entry, err := n.bucket.Get(sessionID)
	if err == nats.ErrKeyNotFound {
		return OutlineNodeConfig{}, false, nil
	}
	if err != nil {
		return OutlineNodeConfig{}, false, err
	}
	var node OutlineNodeConfig
	if err := json.Unmarshal(entry.Value(), &node); err != nil {
		return OutlineNodeConfig{}, false, err
	}
	return node, true, nil
}

func (n *NATSStore) Delete(ctx context.Context, sessionID string) error {
	err := n.bucket.Delete(sessionID)
	if err == nats.ErrKeyNotFound {
		return nil
	}
	return err
}
