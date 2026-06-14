/*
 * ringbuf.h - single-producer/single-consumer byte ring buffer.
 *
 * Purpose: Lock-free SPSC FIFO for IPC between two contexts. Capacity must be a
 * power of two so index wrapping is a cheap mask, not a modulo.
 * Concurrency note: correct for ONE producer and ONE consumer only; head is
 * written solely by the consumer, tail solely by the producer.
 */
#ifndef MINIOS_RINGBUF_H
#define MINIOS_RINGBUF_H

#include <stddef.h>

typedef struct {
    unsigned char *buf;
    size_t mask;   /* capacity - 1 (capacity is a power of two) */
    size_t head;   /* read index  (consumer owns) */
    size_t tail;   /* write index (producer owns) */
} ringbuf_t;

/* Init over `storage` of `capacity` bytes. Returns 0 on success, non-zero if
 * capacity is not a power of two (defensive: required for the mask trick). */
int rb_init(ringbuf_t *rb, unsigned char *storage, size_t capacity);

/* Write up to `n` bytes; returns the number actually written (back-pressure). */
size_t rb_write(ringbuf_t *rb, const unsigned char *data, size_t n);

/* Read up to `n` bytes; returns the number actually read. */
size_t rb_read(ringbuf_t *rb, unsigned char *out, size_t n);

#endif /* MINIOS_RINGBUF_H */
