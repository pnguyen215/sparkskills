# Skills repository — validation, linting and scaffolding toolkit.
# Requires: make (>=3.81), python3 (>=3.9), git.
# Optional: markdownlint-cli2 (npm i -g markdownlint-cli2) for full markdown linting.

SHELL := /bin/sh
.DEFAULT_GOAL := help

PYTHON ?= python3
SKILL_TEMPLATE := templates/SKILL.template.md

.PHONY: help
help: ## Show available targets.
	@printf "Skills repository toolkit\n\n"
	@printf "Targets:\n"
	@awk 'BEGIN { FS = ":.*##" } /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.PHONY: lint
lint: ## Lint markdown formatting and YAML frontmatter (uses markdownlint-cli2 when installed).
	@if command -v markdownlint-cli2 >/dev/null 2>&1; then \
		echo ">> markdownlint-cli2"; \
		markdownlint-cli2 "**/*.md" "#node_modules"; \
	elif command -v markdownlint >/dev/null 2>&1; then \
		echo ">> markdownlint"; \
		markdownlint .; \
	else \
		echo ">> markdownlint not found; running built-in markdown checks"; \
		$(PYTHON) scripts/validate.py --markdown-only; \
	fi

.PHONY: validate
validate: ## Validate every SKILL.md: frontmatter, name/description limits, required sections, placeholders.
	$(PYTHON) scripts/validate.py

.PHONY: check
check: lint validate ## Run lint + validate (CI quality gate).

.PHONY: tree
tree: ## Print the repository structure (excludes .git).
	$(PYTHON) scripts/validate.py --tree

.PHONY: new-skill
new-skill: ## Scaffold a new skill: make new-skill NAME=<category/skill>
	@if [ -z "$(NAME)" ]; then \
		echo "Usage: make new-skill NAME=<category/skill>  (e.g. NAME=testing/contract-testing)"; \
		exit 1; \
	fi; \
	if [ -e "$(NAME)/SKILL.md" ]; then \
		echo "ERROR: $(NAME)/SKILL.md already exists"; \
		exit 1; \
	fi; \
	mkdir -p "$(NAME)"; \
	sed -e "s/{{SKILL_NAME}}/$(notdir $(NAME))/g" \
		-e "s/{{ONE_LINE_DESCRIPTION}}/REPLACE: what it does and when to trigger it/g" \
		"$(SKILL_TEMPLATE)" > "$(NAME)/SKILL.md"; \
	echo "Created $(NAME)/SKILL.md from $(SKILL_TEMPLATE)"; \
	echo "Next: fill in every section, replace all REPLACE markers, then run 'make validate'."

.PHONY: clean
clean: ## Remove lint caches, editor backups and build leftovers.
	@rm -rf .markdownlint-cache .markdownlint-cli2-cache node_modules
	@find . -path ./.git -prune -o -name '*~' -print -o -name '*.bak' -print | while read -r f; do rm -f "$$f"; done
	@echo "Clean."
