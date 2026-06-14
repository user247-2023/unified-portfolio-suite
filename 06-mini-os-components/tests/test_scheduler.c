/*
 * test_scheduler.c - assert-based tests for the round-robin scheduler.
 * Purpose: Prove round-robin ordering, fail-closed registration when the table
 * is full, and that ticking an empty scheduler is a safe no-op.
 */
#include "scheduler.h"

#include <assert.h>
#include <stdio.h>

static int counters[3];

static void task0(void *ctx) { (void)ctx; counters[0]++; }
static void task1(void *ctx) { (void)ctx; counters[1]++; }
static void task2(void *ctx) { (void)ctx; counters[2]++; }

int main(void) {
    scheduler_t s;
    sched_init(&s);

    /* Empty scheduler: ticking must not crash or divide by zero. */
    sched_tick(&s);

    assert(sched_add(&s, task0, NULL) == 0);
    assert(sched_add(&s, task1, NULL) == 0);
    assert(sched_add(&s, task2, NULL) == 0);

    /* One full round: each task runs exactly once, in order. */
    sched_tick(&s); /* task0 */
    sched_tick(&s); /* task1 */
    sched_tick(&s); /* task2 */
    assert(counters[0] == 1 && counters[1] == 1 && counters[2] == 1);

    /* Second round wraps back to task0. */
    sched_tick(&s);
    assert(counters[0] == 2 && counters[1] == 1);

    /* Fill the table to capacity; the next add must fail closed. */
    scheduler_t full;
    sched_init(&full);
    for (int i = 0; i < SCHED_MAX_TASKS; i++) {
        assert(sched_add(&full, task0, NULL) == 0);
    }
    assert(sched_add(&full, task0, NULL) != 0); /* table full -> rejected */

    printf("scheduler tests passed\n");
    return 0;
}
