import time
from pathlib import Path
from search_engine.parser.scorer import FileScorer

def test_scorer_base_weight():
    scorer = FileScorer()
    # a generic file with an unknown extension, not a good dir, recently modified, small size
    path = Path("some_unknown_dir/generic.file")
    weight = scorer.score(path, size_bytes=1000, modified_at=time.time())
    
    # Depth = 2 (depth_boost = 1.0)
    # Ext = .file (weight *= 1)
    # Recent < 7 days (weight *= 1.2)
    # Size < 2MB (weight *= 1)
    # Expected: 1.2
    assert weight == 1.2

def test_scorer_boosts():
    scorer = FileScorer()
    # a priority file in a priority dir
    path = Path("src/main.py")
    weight = scorer.score(path, size_bytes=1000, modified_at=time.time())
    
    # Depth = 2 (depth_boost = 1.0)
    # src dir = 1.3
    # .py ext = 1.5
    # Recency = 1.2
    # Result: 1.0 * 1.3 * 1.5 * 1.2 = 2.34
    assert weight == 2.34

def test_scorer_penalties():
    scorer = FileScorer()
    # a low priority massive file in a bad dir, old
    path = Path("build/logs/output.log")
    weight = scorer.score(path, size_bytes=3_000_000, modified_at=time.time() - 40*24*3600)
    
    # Depth = 3 (depth_boost = 0.666...)
    # build dir = 0.6
    # .log ext = 0.7
    # Old = 1.0
    # Massive = 0.55
    # Result: 0.666... * 0.6 * 0.7 * 1.0 * 0.55 = 0.154 => 0.15
    assert weight == 0.15

def test_scorer_path_depth_boost():
    scorer = FileScorer()
    path = Path("README.md")
    weight = scorer.score(path, size_bytes=1000, modified_at=time.time() - 40*24*3600)
    
    # Depth = 1 (depth_boost = 2.0 / 1 = 2.0)
    # dir = 1.0
    # .md = 1.5
    # Old = 1.0
    # Size = 1.0
    # Result: 2.0 * 1.5 = 3.0
    assert weight == 3.0

def test_scorer_minimum_weight_floor():
    scorer = FileScorer()
    # deep path, bad dir, bad ext, huge file, old
    path = Path("build/a/b/c/d/e/f/g/h/i/output.log")
    weight = scorer.score(path, size_bytes=5_000_000, modified_at=time.time() - 60*24*3600)
    # should never go below 0.1 due to max(0.1, ...) floor
    assert weight >= 0.1

def test_scorer_medium_recency():
    scorer = FileScorer()
    # 15 days old = between 7 and 30 days -> 1.05 multiplier
    path = Path("some_dir/readme.txt")
    weight = scorer.score(path, size_bytes=1000, modified_at=time.time() - 15*24*3600)
    # depth=2 (1.0), no special dir (1.0), .txt=1.5, 15 days=1.05, small=1.0
    # 1.0 * 1.5 * 1.05 = 1.575 => 1.58
    assert weight == 1.58

def test_scorer_high_priority_ext_in_low_priority_dir():
    scorer = FileScorer()
    # A .py file inside node_modules
    path = Path("node_modules/package/setup.py")
    weight = scorer.score(path, size_bytes=500, modified_at=time.time())
    # depth=3 (0.67), node_modules=0.6, .py=1.5, recent=1.2, small=1.0
    # 0.67 * 0.6 * 1.5 * 1.2 = 0.7236 => 0.72
    assert weight == 0.72

def test_scorer_deeply_nested_file():
    scorer = FileScorer()
    path = Path("a/b/c/d/e/f/g/h/i/j/deep.txt")
    weight = scorer.score(path, size_bytes=100, modified_at=time.time())
    # depth=11, depth_boost = 2.0/11 = 0.18 -> max(0.2, 0.18) = 0.2
    # .txt = 1.5, recent = 1.2
    # 0.2 * 1.5 * 1.2 = 0.36
    assert weight == 0.36

def test_scorer_large_file_exactly_at_threshold():
    scorer = FileScorer()
    two_mb = 2 * 1024 * 1024
    path = Path("some/file.txt")
    # exactly at 2MB - should not get penalty only > 2MB is penalized
    weight_at = scorer.score(path, size_bytes=two_mb, modified_at=time.time())
    weight_over = scorer.score(path, size_bytes=two_mb + 1, modified_at=time.time())
    assert weight_at > weight_over

