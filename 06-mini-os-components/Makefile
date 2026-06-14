# -----------------------------------------------------------------------------
# Mini OS Components - build.
# Purpose: Compile components into a static lib and build/run the test harness.
# Security note: hardening flags on by default (stack protector, FORTIFY,
# -Wall -Wextra -Werror) so undefined behavior fails the build, not production.
# -----------------------------------------------------------------------------
CC      ?= cc
CFLAGS  ?= -std=c11 -Wall -Wextra -Werror -O2 -g \
           -fstack-protector-strong -D_FORTIFY_SOURCE=2
INCLUDE := -Iinclude

SRC     := src/allocator.c src/scheduler.c src/ringbuf.c
OBJ     := $(SRC:.c=.o)
LIB     := libminios.a

.PHONY: all test clean
all: $(LIB)

$(LIB): $(OBJ)
	ar rcs $@ $(OBJ)

%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDE) -c $< -o $@

test: $(LIB)
	$(CC) $(CFLAGS) $(INCLUDE) tests/test_allocator.c $(LIB) -o tests/test_allocator
	./tests/test_allocator

clean:
	rm -f $(OBJ) $(LIB) tests/test_allocator
