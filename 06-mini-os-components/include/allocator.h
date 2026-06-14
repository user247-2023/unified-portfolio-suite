/*
 * allocator.h - fixed-block pool allocator interface.
 *
 * Purpose: O(1) allocate/free over a caller-provided, fixed-size block pool.
 * Security trade-off: trades flexibility (one block size) for safety and
 * determinism - no fragmentation, validated frees, predictable latency. Suited
 * to kernel/embedded contexts where general malloc is undesirable.
 */
#ifndef MINIOS_ALLOCATOR_H
#define MINIOS_ALLOCATOR_H

#include <stddef.h>

typedef struct pool pool_t;

/*
 * Initialize a pool over `backing` (size `bytes`) carved into blocks of
 * `block_size`. Returns a pool handle, or NULL on invalid arguments
 * (defensive: rejects zero sizes and overflowing geometry).
 */
pool_t *pool_init(void *backing, size_t bytes, size_t block_size);

/* Allocate one block. Returns NULL when the pool is exhausted (fail-closed). */
void *pool_alloc(pool_t *p);

/*
 * Free a block previously returned by pool_alloc from THIS pool.
 * Rejects pointers outside the pool's range and detects double-free,
 * returning non-zero on such misuse instead of corrupting the free list.
 */
int pool_free(pool_t *p, void *block);

/* Number of currently free blocks (for tests/diagnostics). */
size_t pool_available(const pool_t *p);

#endif /* MINIOS_ALLOCATOR_H */
