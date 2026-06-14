/*
 * allocator.c - fixed-block pool allocator implementation.
 *
 * Design: an intrusive free list. Each free block's first bytes store the
 * index of the next free block, so the pool needs no side metadata array.
 *
 * Security/correctness notes:
 *  - pool_init validates geometry and guards against size_t overflow.
 *  - pool_free validates the pointer is in range and block-aligned, and detects
 *    double-free by scanning the free list (O(n) free, acceptable for the small
 *    pools this is designed for; swap for a per-block bitmap if n is large).
 *  - Freed blocks are poisoned to surface use-after-free during testing.
 */
#include "allocator.h"

#include <stdint.h>
#include <string.h>

#define POOL_NIL ((size_t)-1)
#define POISON   0xDE

struct pool {
    unsigned char *base;
    size_t block_size;
    size_t block_count;
    size_t free_head;   /* index of first free block, or POOL_NIL */
    size_t free_count;
};

/* The pool control block lives at the start of the backing memory. */
pool_t *pool_init(void *backing, size_t bytes, size_t block_size) {
    if (backing == NULL || block_size < sizeof(size_t)) {
        return NULL; /* need room to thread the free-list index */
    }
    if (bytes < sizeof(struct pool) + block_size) {
        return NULL; /* not enough for control block + 1 block */
    }

    pool_t *p = (pool_t *)backing;
    p->base = (unsigned char *)backing + sizeof(struct pool);
    p->block_size = block_size;

    size_t usable = bytes - sizeof(struct pool);
    p->block_count = usable / block_size;
    if (p->block_count == 0) {
        return NULL;
    }

    /* Thread the free list: block i points to block i+1; last -> NIL. */
    for (size_t i = 0; i < p->block_count; i++) {
        size_t *slot = (size_t *)(p->base + i * block_size);
        *slot = (i + 1 < p->block_count) ? (i + 1) : POOL_NIL;
    }
    p->free_head = 0;
    p->free_count = p->block_count;
    return p;
}

void *pool_alloc(pool_t *p) {
    if (p == NULL || p->free_head == POOL_NIL) {
        return NULL; /* fail-closed on exhaustion */
    }
    size_t idx = p->free_head;
    unsigned char *block = p->base + idx * p->block_size;
    p->free_head = *(size_t *)block; /* unlink */
    p->free_count--;
    return block;
}

int pool_free(pool_t *p, void *block) {
    if (p == NULL || block == NULL) {
        return 1;
    }
    unsigned char *b = (unsigned char *)block;
    /* Range check: must point inside the pool. */
    if (b < p->base || b >= p->base + p->block_count * p->block_size) {
        return 2; /* wild pointer */
    }
    size_t offset = (size_t)(b - p->base);
    if (offset % p->block_size != 0) {
        return 3; /* misaligned -> not a real block start */
    }
    size_t idx = offset / p->block_size;

    /* Double-free detection: is this index already on the free list? */
    for (size_t cur = p->free_head; cur != POOL_NIL;
         cur = *(size_t *)(p->base + cur * p->block_size)) {
        if (cur == idx) {
            return 4; /* double free */
        }
    }

    memset(b, POISON, p->block_size); /* surface use-after-free in tests */
    *(size_t *)b = p->free_head;      /* relink */
    p->free_head = idx;
    p->free_count++;
    return 0;
}

size_t pool_available(const pool_t *p) {
    return p ? p->free_count : 0;
}
