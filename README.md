# OWH: OpenWebUI Hybrid

OWH adds Nick's OpenRouter account as a second backend to his local Open WebUI (Docker container `open-webui`, v0.13.3, host network, port 8080), next to the local Ollama (`127.0.0.1:11434`), so the model picker offers local and cloud models and each chat goes to the backend of the model chosen. The deliverable is a small Python CLI, `owh-openrouter` (standard library only at runtime), that stores a dedicated OpenRouter key, manages a curated model allowlist, and writes the OpenRouter connection into Open WebUI's stored config through its admin API (idempotent, with snapshot and `remove`), plus the docs for using, rotating and undoing it.

**Status:** in development. See [`OWH_IMPLEMENTATION_PLAN.md`](OWH_IMPLEMENTATION_PLAN.md) for the phase table and what is done.

## Privacy
Local (Ollama) models stay on the laptop. A chat with an OpenRouter model (shown with an `OR.` prefix) sends the conversation, attached files, RAG excerpts and web-search results to OpenRouter and the upstream model provider.

## Documents
- [Implementation plan](OWH_IMPLEMENTATION_PLAN.md): phases, status, owner questions, phase log
- [Specification](docs/OWH_SPECIFICATION.md): canonical spec (the Amendments override earlier sections)
- [Decisions](docs/OWH_DECISIONS.md): ADR log
- [Architecture](docs/OWH_ARCHITECTURE.md): current and target layout
- [Security policy](SECURITY.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)
