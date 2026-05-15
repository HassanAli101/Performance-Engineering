# Python vs Go

In this folder, I will be trying to get a difference in performance of applications based on their languages. This is inspired from when I was asked in an interview:

> "Ok, so you think go is better than python? why?"

…and a fresh grad me who had his mid semester exams coming up had no real idea of numbers and reasons, just a phrase he had found on a few medium articles he read.

This folder is the first attempt and an intention to look for an answer to that question — **quantitatively, the actual way.**

---

## Setups:

### DB setup:

In all comparisons, a PostgreSQL container is used.

#### Run Postgres:

```bash
docker run --name pg-bench \
  -e POSTGRES_PASSWORD=pass \
  -p 5432:5432 \
  -d postgres:alpine
```

#### Enter psql:

```bash
docker exec -it pg-bench psql -U postgres
```

#### Create table:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT
);
```

#### Insert dummy data:

```sql
INSERT INTO users (name, email)
SELECT 'user' || i, 'user' || i || '@test.com'
FROM generate_series(1, 1000) i;
```

#### Verify:

```sql
SELECT COUNT(*) FROM users;
```

---

### Python setup:

A simple FastAPI application with:

- A hello world endpoint
- A db read endpoint
- A db write endpoint

This framework is chosen because from what I have seen, python is argued to have better dev experience and faster development, over its performance tradeoffs. A majority of companies use python along with FastAPI, so this is done to keep my performance comparison consistent with what **"is" (python + FastAPI)** vs what **"could be" (go + native packages).**

---

### Go Setup:

A simple go application using native `net/http` package (to avoid framework overhead) and pgx for database queries.

It also has:

- A hello world endpoint
- A db read endpoint
- A db write endpoint

---

## Benchmarking

Load testing is done using wrk.

Example:

```bash
wrk -t2 -c20 -d30s http://localhost:8000/hello
```

---

## Results:

### Hello World Endpoint

#### Python Averages (FastAPI, 8 workers)

- ~205 requests/sec
- ~48 ms latency

Cpu Utilization:
![Python_CPU_Util](./results/Default-Hello-World/Python_CPU_Util.png)

Benchmark Results:
![Python_Results](./results/Default-Hello-World/Python_Results.png)

#### Go Averages (net/http, GOMAXPROCS=8)

- ~13.5k requests/sec
- ~0.7 ms latency
- 97% CPU utilization/core

Cpu Utilization:
![Go_CPU_Util](./results/Default-Hello-World/Go_CPU_Util.png)

Benchmark Results:
![Go_Results](./results/Default-Hello-World/Go_Results.png)

### Random userID Read Endpoint:

#### Python Averages (FastAPI, asyncpg)

- ~93 requests/sec
- ~107 ms latency

Benchmark Results:
![Python_Results](./results/DB-Read/Read_Python.png)

#### Go Averages (native, pgxpool)

- ~2.07k requests/sec
- ~5 ms latency
- 97% CPU utilization/core

Benchmark Results:
![Go_Results](./results/DB-Read/Read_Go.png)

### Random userID Email Update Endpoint:

#### Python Averages (FastAPI, asyncpg)

- ~93 requests/sec
- ~108 ms latency

Benchmark Results:
![Python_Results](./results/DB_Update/Update_Python.png)

#### Go Averages (native, pgxpool)

- ~1.1k requests/sec
- ~9 ms latency
- 80% CPU utilization/core

Benchmark Results:
![Go_Results](./results/DB_Update/Update_Go.png)

---

## Observations (initial)

- Go massively outperforms Python in raw throughput (~65x in this setup)
- Go fully utilizes CPU cores, while Python appears to be limited
- Latency in Python is significantly higher even for trivial workloads
- Database operations do not become the bottleneck for python in this setup
- Database Update became a bottleneck for golang application

---

## Hypothesis / Why this happens

Some possible reasons:

- Python is limited by the **Global Interpreter Lock (GIL)**, meaning only one thread executes Python bytecode at a time within a process. This simplifies memory management but restricts true parallel CPU execution in multi-threaded programs.
  - Official Python docs on GIL: https://docs.python.org/3/c-api/init.html#thread-state-and-the-global-interpreter-lock
  - Good explanation (why it exists): https://www.geeksforgeeks.org/python/what-is-the-python-global-interpreter-lock-gil/

---

- Go uses **goroutines** and a runtime scheduler that maps them onto OS threads, allowing it to utilize multiple CPU cores in parallel by default. This enables true concurrent execution for CPU-bound and IO-bound workloads.
  - Go scheduler + goroutines: https://go.dev/doc/effective_go#goroutines
  - GOMAXPROCS (controls parallelism): https://pkg.go.dev/runtime#GOMAXPROCS

---

- FastAPI runs on top of an **ASGI server (uvicorn)**, which introduces additional abstraction layers such as:

  - ASGI interface handling
  - event loop scheduling
  - request parsing and routing

  These layers improve flexibility and developer experience but add runtime overhead compared to lower-level implementations.

  - FastAPI async docs: https://fastapi.tiangolo.com/async/
  - Uvicorn documentation: https://www.uvicorn.org/

---

- Go’s `net/http` package is **closer to the metal and part of the standard library**, meaning:

  - fewer abstraction layers
  - highly optimized request handling
  - tight integration with Go’s runtime and scheduler

  This results in lower latency and higher throughput under load.

  - Go net/http docs: https://pkg.go.dev/net/http

---

- Serialization and request handling in Go is faster due to:

  - **static typing** (no runtime type resolution)
  - **compiled binaries** (no interpreter overhead)
  - more efficient memory layout and allocation patterns

  In contrast, Python performs more work at runtime due to its dynamic nature.

  - Go JSON package: https://pkg.go.dev/encoding/json
  - Python JSON docs: https://docs.python.org/3/library/json.html

---

- Python async (used by FastAPI) is based on an **event loop (cooperative multitasking)**, meaning tasks yield control manually (`await`). While efficient for IO-bound workloads, it does not provide parallel CPU execution within a single process.
  - Python asyncio docs: https://docs.python.org/3/library/asyncio.html

---

- Go uses **preemptive scheduling**, meaning goroutines can be interrupted and rescheduled by the runtime automatically. This leads to better CPU utilization under heavy concurrent workloads compared to cooperative async models.
  - Go scheduler deep dive: https://go.dev/blog/scheduler

---

Some fundamental language/runtime differences explain the large performance gap observed:

- Python is an **interpreted language**, meaning code is executed by an interpreter at runtime rather than being compiled directly into machine code.

  - Python first compiles code to **bytecode**, which is then executed by the Python Virtual Machine (PVM)
  - This introduces overhead on every operation (function calls, loops, object handling)
  - Dynamic typing adds additional runtime cost (type checking, object resolution)

  👉 Result: Slower execution, especially in CPU-bound or high-throughput scenarios

  - Official docs (execution model): https://docs.python.org/3/reference/executionmodel.html
  - Python interpreter internals: https://docs.python.org/3/tutorial/interpreter.html

- Go is a **compiled language**, meaning source code is compiled directly into **native machine code** before execution.

  - The compiled binary runs directly on the CPU
  - No interpreter layer at runtime
  - Static typing allows many optimizations during compilation
  - Efficient memory layout and reduced runtime overhead

  👉 Result: Faster execution, lower latency, and better CPU utilization

  - Go build/compile model: https://go.dev/doc/tutorial/compile-install
  - Effective Go (performance-related concepts): https://go.dev/doc/effective_go

- The relatively similar performance between random reads and random updates suggests that the database itself is likely **not the bottleneck yet**. Simple primary-key lookups and single-row updates in :contentReference[oaicite:0]{index=0} are highly optimized and execute very quickly, especially on a small dataset. As a result, a larger portion of the request time is likely spent in the Python application layer itself, including:
  - request parsing
  - JSON serialization/deserialization
  - async scheduling and event loop overhead
  - database connection acquisition
  - framework abstraction costs

  This means the overall latency is dominated more by the web application runtime than by actual query execution time.

  Documentation:
  - PostgreSQL EXPLAIN ANALYZE: https://www.postgresql.org/docs/current/sql-explain.html  
  - FastAPI async internals: https://fastapi.tiangolo.com/async/  
  - Python asyncio: https://docs.python.org/3/library/asyncio.html  
  - asyncpg docs: https://magicstack.github.io/asyncpg/current/  

---

> **Conclusion:**  
> These differences become most visible in CPU-bound and high-concurrency scenarios, which is why even a simple “hello world” benchmark shows significant divergence.

---
