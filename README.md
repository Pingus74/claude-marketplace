# Claude Marketplace

A curated collection of [Claude Code](https://docs.anthropic.com/claude-code) plugins maintained by Stefano Grechi.

## Available plugins

### Stable

- [**confluence-cli**](plugins/confluence-cli/README.md) — Read, create, update, and search Confluence Cloud pages; upload attachments/images. Auto-activates on Confluence-related prompts. Python 3 stdlib only, cross-platform.

## Getting started

### Add this marketplace

```bash
/plugin marketplace add https://github.com/sgrechi/claude-marketplace
```

Or from a local checkout:

```bash
/plugin marketplace add /path/to/claude-marketplace
```

### Install a plugin

```bash
/plugin install confluence-cli@sgrechi-claude-marketplace
```

### Update the marketplace

```bash
/plugin marketplace update
```

### Remove / uninstall

```bash
/plugin uninstall confluence-cli
/plugin marketplace remove sgrechi-claude-marketplace
```

## Creating a new plugin

Each plugin lives under `plugins/<name>/` with its own `.claude-plugin/plugin.json` manifest. Register it in `.claude-plugin/marketplace.json` under `plugins[]`.

### Canonical plugin structure

```
plugins/my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── skills/         # SKILL.md + scripts + templates + references
├── commands/       # slash commands
├── agents/         # sub-agents
├── hooks/          # event hooks
├── .mcp.json       # MCP server (optional)
└── README.md
```

Use only the subdirectories you need. `confluence-cli` currently uses just `skills/`.

## Repository layout

```
.
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   └── confluence-cli/
│       ├── .claude-plugin/plugin.json
│       ├── skills/confluence-cli/
│       │   ├── SKILL.md
│       │   ├── scripts/
│       │   ├── templates/
│       │   └── references/
│       └── README.md
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Versioning

Each plugin is versioned independently (semver). The marketplace itself has its own version in `.claude-plugin/marketplace.json`. Releases are tagged on the repo as `v<version>`.

## Contributing

PR welcome. Conventions:

- Each plugin in its own directory under `plugins/`, with a `plugin.json` manifest, a `README.md` for humans, and skill/command/agent/hook subdirectories.
- Bump the plugin `version` on any behavior change and note it in `CHANGELOG.md`.
- Flag new/unstable plugins with `"experimental": true` in `marketplace.json` until they're considered stable.
- Scripts should be cross-platform (Python 3 stdlib preferred, or at least POSIX sh + portable equivalents).

## License

MIT — see [LICENSE](LICENSE).
