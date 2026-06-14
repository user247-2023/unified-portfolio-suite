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

TESTS := test_allocator test_scheduler test_ringbuf

test: $(LIB)
	@for t in $(TESTS); do \
	  echo "== building & running $$t =="; \
	  $(CC) $(CFLAGS) $(INCLUDE) tests/$$t.c $(LIB) -o tests/$$t || exit 1; \
	  ./tests/$$t || exit 1; \
	done
	@echo "all mini-os tests passed"

clean:
	rm -f $(OBJ) $(LIB) $(addprefix tests/,$(TESTS))
