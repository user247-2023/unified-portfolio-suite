# -----------------------------------------------------------------------------
# Unified Portfolio Suite - top-level convenience targets.
# Purpose: One command to run every project's test suite. Delegates to the
# cross-platform Python runner so behavior is identical on Linux/macOS/Windows.
# -----------------------------------------------------------------------------
.PHONY: test
test:
	python run_all_tests.py
