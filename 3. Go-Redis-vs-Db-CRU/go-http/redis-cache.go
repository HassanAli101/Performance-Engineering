package main

import (
	"github.com/redis/go-redis/v9"
)

var Rdb = redis.NewClient(&redis.Options{
	Addr: "localhost:6379",
})