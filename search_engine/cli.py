import argparse
import sys
from datetime import datetime
from pathlib import Path

from .widget.widget_factory import create_default_factory
from .widget.widget_observer import WidgetObserver
from .config import load as load_config
from .indexer import Indexer
from .parser.file_parser import FileParser
from .parser.text_extractor import TextExtractor
from .parser.image_extractor import ImageExtractor
from .query.query_engine import QueryEngine
from .query.ranking import (
    RelevanceRanking,
    AlphabeticalRanking,
    DateRanking,
    HistoryRanking,
)
from .query.history import HistoryTracker
from .query.cache import SearchCache, CachedQueryEngine
from .query.query_preprocessor import (
    BaseQueryBuilder,
    SanitizationDecorator,
    SynonymDecorator,
    WildcardDecorator,
)
import os


def cmd_index(args: argparse.Namespace, config: dict) -> None:
    root = Path(args.root or config["indexer"]["root"])

    if not root.exists():
        print(f"Error: root directory '{root}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # select extractors based on the --mode flag
    mode = getattr(args, "mode", "all")
    match mode:
        case "text":
            extractors = [TextExtractor()]
        case "image":
            extractors = [ImageExtractor()]
        case _:
            extractors = [TextExtractor(), ImageExtractor()]

    parser = FileParser(extractors=extractors)
    indexer = Indexer(
        db_path=config["database"]["path"],
        ignore_patterns=config["indexer"]["ignore"],
        parser=parser,
    )

    processes = getattr(args, "processes")
    if processes is None:
        processes = (
            os.cpu_count() or 1
        )  # safety to put 1 in here and also get rid of warnings

    # cap it to os.cpu_count(), in case the user wants to introduce more
    processes = min(processes, os.cpu_count())

    print(f"Indexing '{root}' (mode: {mode}, processes: {processes}) ")
    report = indexer.run(root, num_processes=processes)
    print(report.print_report())

    cache = SearchCache(config["database"]["path"])
    cache.invalidate()  # invalidate when indexing is run
    print("Search cache cleared.")


def cmd_search(args: argparse.Namespace, config: dict) -> None:
    query = " ".join(args.query)
    tracker = HistoryTracker(config["database"]["path"])
    match getattr(args, "sort", "relevance"):
        case "alphabetical":
            strategy = AlphabeticalRanking()
        case "date":
            strategy = DateRanking()
        case "history":
            strategy = HistoryRanking(tracker)
        case _:
            strategy = RelevanceRanking()

    # build the decorator chain: Sanitization -> Synonyms -> Wildcards
    builder = WildcardDecorator(
        SynonymDecorator(SanitizationDecorator(BaseQueryBuilder()))
    )

    engine = QueryEngine(
        db_path=config["database"]["path"],
        max_results=config["search"]["max_results"],
        snippet_tokens=config["search"]["snippet_tokens"],
        strategy=strategy,
        builder=builder,
    )
    engine.attach(tracker)

    # set up the widget system factory and observer
    widget_factory = create_default_factory()
    widget_observer = WidgetObserver(widget_factory)
    engine.attach(widget_observer)  # subscribe to search result updates

    ttl = config["search"].get("cache_ttl", 300)  # get the time to live
    cache = SearchCache(config["database"]["path"], ttl_seconds=ttl)
    cached_engine = CachedQueryEngine(engine, cache)
    results = cached_engine.search(query)

    if not results:
        print("No results found.")
        return

    cache_label = (
        " (cached)" if cache.get_last_hit() else ""
    )  # print result to show if the data is cached or not
    print(f"\n{len(results)} result(s) for '{query}'{cache_label}\n{'─' * 50}")

    for i, result in enumerate(results, start=1):
        modified = datetime.fromtimestamp(result.modified_at).strftime("%Y-%m-%d %H:%M")
        print(f"\n[{i}] {result.filename}")
        print(f"    {result.path}")
        print(f"    Score    : {result.score:.1f}")
        print(f"    Modified : {modified}")
        if result.preview:
            print(f"    Preview  : {result.preview}")

    # display widgets already evaluated by the observer
    active_widgets = widget_observer.get_active_widgets()
    ctx = widget_observer.get_last_context()

    if active_widgets and ctx:
        box_width = 42
        print(f"\n+{'-' * box_width}+")
        for idx, widget in enumerate(active_widgets):
            for line in widget.render(ctx).splitlines():
                print(f"| {line:<{box_width - 1}}|")
            if idx < len(active_widgets) - 1:
                print(f"+{'-' * box_width}+")
        print(f"+{'-' * box_width}+")


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
    index_cmd.add_argument(
        "--mode",
        choices=["all", "text", "image"],
        default="all",
        help="Index only specific file types (all, text, image)",
    )
    index_cmd.add_argument(
        "--processes",
        type=int,
        help="Number of producer processes to use for indexing",
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
    Restrict the search to a specific area using 'path:', 'content:', or 'color:'.
     -search content: whatever
     -search path:src
     -search color:red

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

    suggest_cmd = subparsers.add_parser(
        "suggest", help="Suggest queries based on history"
    )
    suggest_cmd.add_argument("query", nargs="+", help="Prefix to search for in history")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path) if config_path else load_config()

    match args.command:
        case "index":
            cmd_index(args, config)
        case "search":
            cmd_search(args, config)
        case "suggest":
            cmd_suggest(args, config)
