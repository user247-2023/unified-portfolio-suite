/*
 * scheduler.c - cooperative round-robin scheduler.
 * Defensive notes: sched_add fails closed when the table is full; sched_tick is
 * a no-op when there are no active tasks (no division/modulo by zero).
 */
#include "scheduler.h"

void sched_init(scheduler_t *s) {
    if (s == NULL) return;
    s->count = 0;
    s->cursor = 0;
    for (size_t i = 0; i < SCHED_MAX_TASKS; i++) {
        s->tasks[i].active = 0;
    }
}

int sched_add(scheduler_t *s, task_fn fn, void *ctx) {
    if (s == NULL || fn == NULL || s->count >= SCHED_MAX_TASKS) {
        return 1; /* fail-closed */
    }
    s->tasks[s->count].fn = fn;
    s->tasks[s->count].ctx = ctx;
    s->tasks[s->count].active = 1;
    s->count++;
    return 0;
}

void sched_tick(scheduler_t *s) {
    if (s == NULL || s->count == 0) return;
    for (size_t scanned = 0; scanned < s->count; scanned++) {
        size_t idx = s->cursor % s->count;
        s->cursor = (s->cursor + 1) % s->count;
        if (s->tasks[idx].active) {
            s->tasks[idx].fn(s->tasks[idx].ctx);
            return;
        }
    }
}
