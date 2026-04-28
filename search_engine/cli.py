import argparse
import sys
from datetime import datetime
from pathlib import Path
from .config import load as load_config
from .indexer import Indexer
from .query.query_engine import QueryEngine
from .query.ranking import RelevanceRanking, AlphabeticalRanking, DateRanking, HistoryRanking
from .query.history import HistoryTracker
from .query.cache import SearchCache, CachedQueryEngine


def cmd_index(args: argparse.Namespace, config: dict) -> None:
    root = Path(args.root or config["indexer"]["root"])

    if not root.exists():
        print(f"Error: root directory '{root}' does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"Indexing '{root}' ...")

    indexer = Indexer(
        db_path=config["database"]["path"],
        ignore_patterns=config["indexer"]["ignore"],
    )
    report = indexer.run(root)
    print(report.print_report())

    cache = SearchCache(config["database"]["path"])
    cache.invalidate() #invalidate when indexing is run
    print("Search cache cleared.")


def cmd_search(args: argparse.Namespace, config: dict) -> None:
    query = " ".join(args.query)
    tracker = HistoryTracker(config["database"]["path"])
    match getattr(args, "sort", "relevance"):
        case "alphabetical": strategy = AlphabeticalRanking()
        case "date": strategy = DateRanking()
        case "history": strategy = HistoryRanking(tracker)
        case _: strategy = RelevanceRanking()

    engine = QueryEngine(
        db_path=config["database"]["path"],
        max_results=config["search"]["max_results"],
        snippet_tokens=config["search"]["snippet_tokens"],
        strategy=strategy,
    )
    engine.attach(tracker)

    ttl = config["search"].get("cache_ttl", 300) # get the time to live
    cache = SearchCache(config["database"]["path"], ttl_seconds=ttl)
    cached_engine = CachedQueryEngine(engine, cache)
    results = cached_engine.search(query)

    if not results:
        print("No results found.")
        return

    cache_label = " (cached)" if cache.get_last_hit() else "" #print result to show if the data is cached or not
    print(f"\n{len(results)} result(s) for '{query}'{cache_label}\n{'─' * 50}")

    for i, result in enumerate(results, start=1):
        modified = datetime.fromtimestamp(result.modified_at).strftime("%Y-%m-%d %H:%M")
        print(f"\n[{i}] {result.filename}")
        print(f"    {result.path}")
        print(f"    Score    : {result.score:.1f}")
        print(f"    Modified : {modified}")
        if result.preview:
            print(f"    Preview  : {result.preview}")


def cmd_suggest(args: argparse.Namespace, config: dict) -> None:
    tracker = HistoryTracker(config["database"]["path"])
    prefix = " ".join(args.query)
    suggestions = tracker.get_suggestions(prefix)
    
    if not suggestions:
        print(f"No suggestions found for '{prefix}'.")
        return
        
    print(f"Suggestions for '{prefix}':")
    for s in suggestions:
        print(f"  - {s}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="search-engine",
        description="Local file search engine",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to a custom config.toml",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    index_cmd = subparsers.add_parser("index", help="Crawl and index files")
    index_cmd.add_argument(
        "--root",
        metavar="PATH",
        help="Root directory to crawl",
    )

    search_help = """
Search the index.
Examples of specific queries that you may input

Terminal Escaping:
  If your search uses double quotes (""), wrap the ENTIRE query in single quotes ('') 

->> Basic Searches (No quotes needed)
    Finds files containing all words anywhere (path, name, or content).
     -search hello world

->> Specific Column Searches
    Restrict the search to a specific area using 'path:' or 'content:'.
     -search content: whatever
     -search path:src

->> Exact Phrase Searches (Needs single quotes in terminal)
    Find an exact, multi-word sequence (including spaces). 
     -search '"hello world"'
     -search 'content:"void main()"'

->> Advanced Combinations (AND Logic)
    Mix and match qualifiers. All conditions must be met.
     -search 'path:src content:"whatever i want"'
     -search path:tests content:import content:os
"""

    search_cmd = subparsers.add_parser(
        "search",
        help="Search the local index",
        description=search_help,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    search_cmd.add_argument(
        "query",
        nargs="+",
        help="Search query terms",
    )
    search_cmd.add_argument(
        "--sort",
        choices=["relevance", "alphabetical", "date", "history"],
        default="relevance",
        help="Ranking strategy to use (relevance, alphabetical, date, history)",
    )

    suggest_cmd = subparsers.add_parser("suggest", help="Suggest queries based on history")
    suggest_cmd.add_argument("query", nargs="+", help="Prefix to search for in history")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path) if config_path else load_config()

    match args.command:
        case "index":  cmd_index(args, config)
        case "search": cmd_search(args, config)
        case "suggest": cmd_suggest(args, config)
