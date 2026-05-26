# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - Iteration 3 (2026-05-22)

Final major release focusing on performance, UI enhancements, and multi-modal capabilities.

### Added
- **Concurrency**: Implemented a highly optimized Producer-Consumer architecture using multiple `multiprocessing` worker processes for file parsing and a single Thread for safe SQLite database writes.
- **Code Quality**: Added `pre-commit` hooks with `black` to enforce standard Python formatting and trailing whitespace rules.
- **Query Pipeline**: Implemented a decorator-based query pipeline (Sanitization -> Synonyms -> Wildcards) for robust search processing.
- **Dynamic UI Widgets**: Built a context-aware widget system utilizing Factory and Observer design patterns to display different results dynamically.
- **Multi-modal Search**: Added support for extracting and searching by dominant image colors using KMeans clustering.

### Changed
- **CLI Options**: Refactored the CLI to include a `--mode` flag to selectively index `text`, `image`, or `all` file types.

## [0.2.0] - Iteration 2 (2026-04-28)

Second iteration focusing on search quality, history tracking, and retrieval speed.

### Added
- **Caching**: Implemented fast search retrieval via an on-disk SQLite cache using the Proxy design pattern.
- **Ranking System**: Added Swappable Ranking Algorithms (Relevance, Alphabetical, Date, History) and ranking heuristics at index time.
- **Search History**: Implemented a Search History Observer for tracking user queries and popularity.
- **Testing**: Added comprehensive `pytest` test suites for the query parser and scoring engine.

### Changed
- **Query Parser**: Rewrote the query parser to build structured SQLite FTS5 queries instead of simple text matches.
- **Result Formatting**: Refactored the CLI result formatter to elegantly display preview snippets and colors.
- **Database Schema**: Added the exact file path into the FTS virtual tables to improve search accuracy.

## [0.1.0] - Iteration 1 (2026-04-01)

Initial prototype release establishing the core search engine architecture.

### Added
- **Core Engine**: Fully implemented the initial `Indexer`, `QueryEngine`, and `FileWalker` with pattern filtering.
- **Database**: Created the main SQLite connection manager, core schema, and FTS5 index.
- **Parser**: Implemented the generic file parser with basic text extractors and timestamp change detection.
- **Configuration**: Added default TOML configuration and loader.
- **CLI**: Finalized the basic command line interface.
- **Documentation**: Initialized the Python package structure and created the first 3 levels of the C4 Architecture diagrams.

### Fixed
- **Extraction**: Added error replacement (`errors="replace"`) to the text parser to prevent the engine from crashing on binary files or weird encodings.
