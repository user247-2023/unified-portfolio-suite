# Mini Operating System Components

Educational, from-scratch implementations of core operating-system building
blocks in C: a fixed-pool memory allocator, a round-robin task scheduler, and a
ring-buffer IPC queue. The goal is clarity and correctness, not replacing libc.

## Problem

OS concepts (allocation, scheduling, synchronization) are easy to use and hard
to truly understand. Reading about a slab allocator or a scheduler isn't the
same as implementing one, handling the edge cases, and proving it works.

## Solution

Three small, independently testable components, each with a clean header
interface and a focus on the tricky parts:

- **`allocator`** — a fixed-block pool allocator (free-list based) that avoids
  fragmentation and runs in O(1) for alloc/free.
- **`scheduler`** — a cooperative round-robin scheduler over a fixed task table.
- **`ringbuf`** — a single-producer/single-consumer lock-free ring buffer for IPC.

## Tech Stack

- **C (C11)** — manual memory management is the point.
- **Make** — build + test.
- A tiny assert-based test harness (no external framework) keeps it portable.

## Usage

```bash
make            # build the static library (libminios.a)
make test       # build & run the assert-based tests for all three components
make clean
```

`make test` compiles and runs `test_allocator`, `test_scheduler`, and
`test_ringbuf` with hardening flags (`-Wall -Wextra -Werror`,
`-fstack-protector-strong`, `-D_FORTIFY_SOURCE=2`), so undefined behavior fails
the build. The suite is exercised in CI on Linux/GCC.

## Security Considerations

- **Bounds checking by contract.** The allocator validates that a pointer being
  freed belongs to its pool (rejecting wild/double frees) rather than trusting
  the caller.
- **No undefined behavior on exhaustion.** `pool_alloc` returns `NULL` when the
  pool is full; callers must check (fail-closed) — demonstrated in the tests.
- **Integer-overflow safety.** Size/index math is checked before use to avoid
  the classic allocator overflow → heap-corruption bug class.
- **Defensive zeroing.** Freed blocks are poisoned in debug builds to surface
  use-after-free during testing.

## Lessons Learned

- A fixed-block pool sidesteps fragmentation entirely — the right trade-off when
  allocation sizes are known and predictable (embedded/kernel contexts).
- Validating freed pointers against the pool's address range turned a whole
  class of memory-corruption bugs into clean, early `NULL`/abort paths.
- Writing the tests first forced the interfaces to be small and total.
