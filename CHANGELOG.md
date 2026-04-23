# Changelog

All notable changes to this marketplace are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/), and the marketplace and each plugin adhere to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0] - 2026-04-23

### Changed
- **confluence-cli** promoted to **stable** (removed `experimental` flag in marketplace).
- Marketplace bumped to 1.0.0 alongside the first stable plugin.

### Fixed
- **confluence-cli** `list-folder`: the v2 endpoint `GET /folders/{id}/children` returned 404. Re-implemented on top of v1 `/content/{id}/child/page` + `/content/{id}/child/folder`, aggregating both in a single simplified response (`pages[]`, `folders[]`, `total`). **Breaking change on output shape vs 0.1.x** — justified by the 1.0.0 API commitment.
- **confluence-cli** `load_credentials` error message: no longer hardcodes `~/.claude/skills/...`. Resolves the actual `setup.py` path at runtime via `Path(__file__).with_name('setup.py')`, so the hint works both for plugin installs and for local user-skill copies.

### Verified
- End-to-end test pass against Confluence Cloud for all 11 commands: `whoami`, `get-space`, `get-page`, `list-children`, `list-folder` (fixed), `search`, `create-page`, `update-page` (with auto version bump), `delete-page`, `list-attachments`, `upload-attachment` (multipart).

## [0.1.1] - 2026-04-23

### Changed
- **confluence-cli** plugin: reworded README and SKILL.md to reflect plugin terminology (was drafted as a user skill). Install instructions now lead with `/plugin marketplace add` + `/plugin install` and clarify that slash commands live in the Claude Code chat (not the terminal).
- Replaced hardcoded `~/.claude/skills/confluence-cli/...` paths with dynamic discovery via `find ~/.claude -name <script> -path '*confluence-cli*'`, so the skill works regardless of install location (plugin cache vs local skills folder).

## [0.1.0] - 2026-04-23

### Added
- Initial marketplace scaffold (`.claude-plugin/marketplace.json`, layout, docs).
- `confluence-cli` plugin **v0.1.0** (experimental):
  - 11 commands covering read/write/search/attachments against Confluence Cloud v2 REST API.
  - Interactive credential setup script with token validation.
  - Cross-platform (Python 3 stdlib only).
  - Three storage-format templates (spec-api, flow-doc, adr).
  - Storage format cheatsheet for writing pages.
