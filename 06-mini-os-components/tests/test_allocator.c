/*
 * test_allocator.c - assert-based unit tests for the pool allocator.
 * Purpose: Prove the safety contracts: exhaustion returns NULL, frees recycle
 * blocks, and double/wild frees are rejected rather than corrupting state.
 */
#include "allocator.h"

#include <assert.h>
#include <stdio.h>

int main(void) {
    static unsigned char backing[1024];
    pool_t *p = pool_init(backing, sizeof(backing), 64);
    assert(p != NULL);

    size_t cap = pool_available(p);
    assert(cap > 0);

    /* Allocate everything; pool must then fail closed. */
    void *blocks[64];
    size_t n = 0;
    void *b;
    while ((b = pool_alloc(p)) != NULL) {
        blocks[n++] = b;
    }
    assert(n == cap);
    assert(pool_alloc(p) == NULL);        /* exhaustion -> NULL */

    /* Free one and reallocate. */
    assert(pool_free(p, blocks[0]) == 0);
    assert(pool_available(p) == 1);
    assert(pool_alloc(p) != NULL);

    /* Double free is rejected. */
    void *x = blocks[1];
    assert(pool_free(p, x) == 0);
    assert(pool_free(p, x) == 4);         /* second free -> double-free code */

    /* Wild pointer is rejected. */
    int stack_var = 0;
    assert(pool_free(p, &stack_var) == 2);

    printf("allocator tests passed (%zu blocks)\n", cap);
    return 0;
}
