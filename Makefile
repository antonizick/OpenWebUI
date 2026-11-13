SHELL := /bin/bash
LAUNCHER := $(HOME)/.local/bin/owh-openrouter
ROOT := $(CURDIR)
SH_FILES := $(shell git ls-files "scripts/*.sh" "scripts/git-hooks/*")

.PHONY: check test lint install uninstall

check: test lint

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .
	shellcheck $(SH_FILES)
	gitleaks detect --no-banner

# Writes a launcher that runs the repo in place (ADR-0010). Not run by any build phase before 05.
install:
	@mkdir -p $(dir $(LAUNCHER))
	@printf '#!/usr/bin/env bash\nexec uv run --project %s owh-openrouter "$$@"\n' '$(ROOT)' > $(LAUNCHER)
	@chmod 755 $(LAUNCHER)
	@echo "installed $(LAUNCHER)"

uninstall:
	rm -f $(LAUNCHER)
