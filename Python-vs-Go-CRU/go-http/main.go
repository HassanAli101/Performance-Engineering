package main

import (
	"fmt"
	"github.com/jackc/pgx/v5"
	"math/rand/v2"
	"net/http"
)

type User struct {
	id    int
	name  string
	email string
}

func main() {
	http.HandleFunc("/hello", helloWorld)
	http.HandleFunc("/getRandomUser", ReadUserID)
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
