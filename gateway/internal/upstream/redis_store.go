package upstream

import (
	"context"
	"encoding/json"
	"time"

	"github.com/redis/go-redis/v9"
)

type RedisStore struct {
	client    *redis.Client
	ttl       time.Duration
	keyPrefix string
}

func NewRedisStore(client *redis.Client, ttl time.Duration) *RedisStore {
	prefix := "outline:sessions"
	return &RedisStore{client: client, ttl: ttl, keyPrefix: prefix}
}

func (r *RedisStore) key(sessionID string) string {
	return r.keyPrefix + ":" + sessionID
}

func (r *RedisStore) Save(ctx context.Context, sessionID string, node OutlineNodeConfig) error {
	payload, err := json.Marshal(node)
	if err != nil {
		return err
	}
	return r.client.Set(ctx, r.key(sessionID), payload, r.ttl).Err()
}

func (r *RedisStore) Load(ctx context.Context, sessionID string) (OutlineNodeConfig, bool, error) {
	value, err := r.client.Get(ctx, r.key(sessionID)).Result()
	if err == redis.Nil {
		return OutlineNodeConfig{}, false, nil
	}
	if err != nil {
		return OutlineNodeConfig{}, false, err
	}
	var node OutlineNodeConfig
	if err := json.Unmarshal([]byte(value), &node); err != nil {
		return OutlineNodeConfig{}, false, err
	}
	return node, true, nil
}

func (r *RedisStore) Delete(ctx context.Context, sessionID string) error {
	return r.client.Del(ctx, r.key(sessionID)).Err()
}
