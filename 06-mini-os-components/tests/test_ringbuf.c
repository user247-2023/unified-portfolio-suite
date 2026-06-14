/*
 * test_ringbuf.c - assert-based tests for the SPSC ring buffer.
 * Purpose: Prove power-of-two validation, write/read round-trips, back-pressure
 * (never overrun unread data), and correct index wrap-around.
 */
#include "ringbuf.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    unsigned char storage[8];
    ringbuf_t rb;

    /* Non-power-of-two capacity must be rejected. */
    assert(rb_init(&rb, storage, 7) != 0);
    assert(rb_init(&rb, storage, 8) == 0);

    /* Basic write/read round-trip. */
    const unsigned char in[] = {1, 2, 3, 4};
    assert(rb_write(&rb, in, 4) == 4);
    unsigned char out[4] = {0};
    assert(rb_read(&rb, out, 4) == 4);
    assert(memcmp(in, out, 4) == 0);

    /* Back-pressure: capacity is 8, so a 10-byte write stores only 8. */
    const unsigned char big[10] = {9, 9, 9, 9, 9, 9, 9, 9, 9, 9};
    assert(rb_write(&rb, big, 10) == 8);

    /* Reading fewer than available leaves the rest buffered. */
    unsigned char part[3] = {0};
    assert(rb_read(&rb, part, 3) == 3);

    /* Wrap-around: write across the buffer boundary and read it back intact. */
    unsigned char drain[8];
    rb_read(&rb, drain, 8);                 /* empty it */
    const unsigned char seq[6] = {10, 11, 12, 13, 14, 15};
    assert(rb_write(&rb, seq, 6) == 6);
    unsigned char back[6] = {0};
    assert(rb_read(&rb, back, 6) == 6);
    assert(memcmp(seq, back, 6) == 0);

    printf("ringbuf tests passed\n");
    return 0;
}
