# Contributing to AI-IN Peter

"The more people working on this, the better my poker game gets." — Peter, probably

## Quick Start

1. Fork → Clone → `bash scripts/setup.sh`
2. Branch: `git checkout -b feature/my-feature`
3. Code → Test locally with `npm start`
4. PR with description of what you changed and why

## Ideas for Contributions

### High Priority
- **Twitch chat integration** — Viewers vote on Peter's decisions
- **Voice synthesis** — Peter narrates decisions via ElevenLabs/TTS
- **Hand replay viewer** — Browse past hands with Peter's reasoning
- **Session analytics** — P&L charts, win rate over time

### Engine
- **Better GTO tables** — More granular pre-computed strategies
- **Local vision model** — YOLO/OCR for card detection without API costs
- **Multi-casino support** — Adapt vision to different casino UIs

### Personality
- **Custom personas** — Swap Peter for other character archetypes
- **Quote packs** — Themed quote sets (movie quotes, sports, etc.)
- **Dynamic personality** — Peter gets more degenerate when winning, cautious when losing

### UI
- **Themes** — Custom overlay color schemes
- **Compact mode** — Minimal overlay for smaller screens
- **Sound effects** — Audio cues for decisions

## Code Style

- **React**: Functional components, inline styles for overlay perf, hooks
- **Python**: PEP 8, type hints, async/await for I/O
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`)
- **Peter quotes**: Keep them PG-13 and poker-related

## License

MIT. By contributing, your code falls under the same license.
