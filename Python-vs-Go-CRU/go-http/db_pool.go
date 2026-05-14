package main

import (
	"context"
	"log"
	"os"
	"sync"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/joho/godotenv"
)

var (
	pgInstance *pgxpool.Pool
	pgOnce     sync.Once
)

func CreateDbPool() *pgxpool.Pool {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}

	pgOnce.Do(func() {
		pool, err := pgxpool.New(context.Background(), os.Getenv("DATABASE_URL"))
		if err != nil {
			log.Println("Unable to create DB pool")
		}
		pgInstance = pool
	})
	return pgInstance
}
