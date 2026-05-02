# Performance-Engineering

A fun little repo that I want to use to implement and understand performance engineering in software systems. Documenting my experience along the way.

Thanks to youtube videos for inspiring me on a random saturday
[Lets handle 1 million RPS](https://youtu.be/W4EwfEU8CGA?si=EqBLescHYaTUUH-U)
[Intro and Matrix Multiplication](https://youtu.be/o7h_sYMk_oc?si=1vGV47rqlz5gdLtB)

## My System

The system has 4 physical cores and 8 logical threads. Benchmarks were tuned to match physical core count for fair comparison, while also exploring oversubscription effects.
