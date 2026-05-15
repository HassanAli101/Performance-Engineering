package main

import (
	"fmt"
	"math/rand/v2"
	"net/http"

	"github.com/jackc/pgx/v5"
)

type User struct {
	id    int
	name  string
	email string
}

func main() {
	http.HandleFunc("/hello", helloWorld)
	http.HandleFunc("/getRandomUser", ReadUserID)
	http.HandleFunc("/updateRandomUser", UpdateUserEmail)
	http.HandleFunc("/PopulateRedis", PopulateRedis)
	http.HandleFunc("/flushRedisToDB", FlushRedisToDB)
	http.HandleFunc("/getRandomUserCached", ReadUserIDCache)
	http.HandleFunc("/updateRandomUserCached", UpdateUserEmailCache)
	http.ListenAndServe(":8080", nil)
}

func helloWorld(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Hello World")
}

func ReadUserID(w http.ResponseWriter, r *http.Request) {
	pool := CreateDbPool()
	userID := rand.IntN(1000)
	query := `Select * from users where id = @userID;`
	args := pgx.NamedArgs{
		"userID": userID,
	}
	var user User
	err := pool.QueryRow(r.Context(), query, args).Scan(&user.id, &user.name, &user.email)
	if err != nil {
		fmt.Fprintf(w, "got an error in query row %s", err)
		return
	}
	fmt.Fprintf(w, "got the user: %v\n", user)
}

func UpdateUserEmail(w http.ResponseWriter, r*http.Request) {
	pool := CreateDbPool()
	userID := rand.IntN(1000)
	query := `Update users set email = @newEmail where id = @userID;`
	args := pgx.NamedArgs{
		"newEmail": fmt.Sprintf("updated_user_%d@newtest.com", userID),
		"userID": userID,
	}
	commandTag, err := pool.Exec(r.Context(), query, args)
	if err != nil {
		fmt.Fprintf(w, "got an error in query row %s", err)
		return
	}
	if commandTag.RowsAffected() != 1 {
		fmt.Fprintf(w,"No row found to update")
		return
	}
	fmt.Fprintf(w, "updated the user: %d\n", userID)
}

func PopulateRedis(w http.ResponseWriter, r * http.Request) {
	pool := CreateDbPool()
	var id int
	var name string
	var email string
	rows, _ := pool.Query(r.Context(), "Select id, name, email from users")
	for rows.Next() {
		rows.Scan(&id ,&name, &email)
		Rdb.HSet(r.Context(), fmt.Sprintf("user:%d", id), map[string]interface{} {
			"name": name,
			"email": email,
		})
	}
	fmt.Fprintf(w, "Populated cache")
}

func ReadUserIDCache(w http.ResponseWriter, r * http.Request) {
	userID := rand.IntN(1000)
	user, _ := Rdb.HGetAll(r.Context(), fmt.Sprintf("user:%d", userID)).Result()
	fmt.Fprintf(w, "got the user: %v\n", user)
}

func UpdateUserEmailCache(w http.ResponseWriter, r * http.Request) {
	userID := rand.IntN(1000)
	_ = Rdb.HSet(r.Context(), fmt.Sprintf("user:%d", userID), "email", fmt.Sprintf("updated-email-user:%d@cached.com", userID))
	fmt.Fprintf(w, "updated email for user: %d\n", userID)
}

func FlushRedisToDB(w http.ResponseWriter, r *http.Request) {
	pool := CreateDbPool()

	iter := Rdb.Scan(r.Context(), 0, "user:*", 0).Iterator()

	flushed := 0

	for iter.Next(r.Context()) {
		key := iter.Val()

		// read redis hash
		data, err := Rdb.HGetAll(r.Context(), key).Result()
		if err != nil {
			fmt.Fprintf(w, "redis read error for %s: %v\n", key, err)
			continue
		}

		// extract id from key: "user:123"
		var id int
		_, err = fmt.Sscanf(key, "user:%d", &id)
		if err != nil {
			fmt.Fprintf(w, "key parse error %s: %v\n", key, err)
			continue
		}

		name := data["name"]
		email := data["email"]

		// UPSERT into postgres
		query := `
			INSERT INTO users (id, name, email)
			VALUES (@id, @name, @email)
			ON CONFLICT (id)
			DO UPDATE SET
				name = EXCLUDED.name,
				email = EXCLUDED.email;
		`

		_, err = pool.Exec(r.Context(), query, pgx.NamedArgs{
			"id":    id,
			"name":  name,
			"email": email,
		})

		if err != nil {
			fmt.Fprintf(w, "db write error for %s: %v\n", key, err)
			continue
		}

		flushed++
	}

	if err := iter.Err(); err != nil {
		fmt.Fprintf(w, "scan error: %v\n", err)
		return
	}

	fmt.Fprintf(w, "flushed %d users from redis to db\n", flushed)
}