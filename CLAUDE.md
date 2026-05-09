# schwab-core

Shared broker-agnostic utility library used as a git dependency by `trade-helper`, `finimal-mobile`, `finimal-gamma-service`, `spx-gex`, and `expected-move-analysis`.

## Stack

- **Python >=3.11**, Poetry
- Zero runtime dependencies (pure Python)
- pytest + pytest-cov for tests

## Layout

```
schwab_core/
  broker/        Broker API adapters
  calculations/  Greeks, P/L, expected move math
  position/      Position classification and modeling
  strategy/      Strategy detection (iron condor, butterfly, etc.)
  symbol/        Symbol parsing utilities
  transformers/  Data transformation helpers
  utils/         Shared utilities
examples/        Usage examples
tests/           pytest suite
```

## Key Commands

```bash
poetry install
poetry run pytest
```

## Usage in Dependent Repos

Installed as a git dep:
```toml
schwab-core = {git = "https://github.com/phamdt/schwab-core.git", branch = "refactor/proper-poetry-package"}
```

Or for local development (finimal-gamma-service uses `-e ../schwab-core`).

## GitHub

`phamdt/schwab-core` (public) — default branch: `main`
