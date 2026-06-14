/*
 * scheduler.h - cooperative round-robin scheduler interface.
 *
 * Purpose: Cycle a fixed table of tasks, each a function pointer + state, in
 * round-robin order. Cooperative (tasks run to a yield point) keeps it portable
 * and free of the reentrancy hazards of preemption - the right trade-off for an
 * educational/embedded core.
 */
#ifndef MINIOS_SCHEDULER_H
#define MINIOS_SCHEDULER_H

#include <stddef.h>

#define SCHED_MAX_TASKS 16

typedef void (*task_fn)(void *ctx);

typedef struct scheduler scheduler_t;

void sched_init(scheduler_t *s);

/* Register a task. Returns 0 on success, non-zero if the table is full. */
int sched_add(scheduler_t *s, task_fn fn, void *ctx);

/* Run one round-robin tick (advances to and runs the next runnable task). */
void sched_tick(scheduler_t *s);

/* Opaque type definition kept here so callers can stack-allocate one. */
struct scheduler {
    struct { task_fn fn; void *ctx; int active; } tasks[SCHED_MAX_TASKS];
    size_t count;
    size_t cursor;
};

#endif /* MINIOS_SCHEDULER_H */
