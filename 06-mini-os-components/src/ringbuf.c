/*
 * ringbuf.c - SPSC byte ring buffer.
 * Defensive notes: rb_init rejects non-power-of-two capacities; read/write are
 * bounded by available space so they can never overrun the backing storage.
 */
#include "ringbuf.h"

static int is_power_of_two(size_t x) {
    return x != 0 && (x & (x - 1)) == 0;
}

int rb_init(ringbuf_t *rb, unsigned char *storage, size_t capacity) {
    if (rb == NULL || storage == NULL || !is_power_of_two(capacity)) {
        return 1;
    }
    rb->buf = storage;
    rb->mask = capacity - 1;
    rb->head = 0;
    rb->tail = 0;
    return 0;
}

static size_t rb_used(const ringbuf_t *rb) {
    return rb->tail - rb->head;
}

size_t rb_write(ringbuf_t *rb, const unsigned char *data, size_t n) {
    size_t capacity = rb->mask + 1;
    size_t space = capacity - rb_used(rb);
    if (n > space) n = space; /* back-pressure: never overwrite unread data */
    for (size_t i = 0; i < n; i++) {
        rb->buf[rb->tail & rb->mask] = data[i];
        rb->tail++;
    }
    return n;
}

size_t rb_read(ringbuf_t *rb, unsigned char *out, size_t n) {
    size_t used = rb_used(rb);
    if (n > used) n = used;
    for (size_t i = 0; i < n; i++) {
        out[i] = rb->buf[rb->head & rb->mask];
        rb->head++;
    }
    return n;
}
