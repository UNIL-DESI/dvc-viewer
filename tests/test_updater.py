import sys
from pathlib import Path
import pytest
import yaml

from dvc_viewer.updater import _resolve_foreach_items

def test_resolve_foreach_items_from_vars(tmp_path):
    """Should resolve variables defined in dvc.yaml vars."""
    dvc_data = {
        "vars": [
            {"datasets": ["movielens", "lastfm"]}
        ]
    }
    resolved = _resolve_foreach_items("${datasets}", tmp_path, dvc_data)
    assert resolved == ["movielens", "lastfm"]

def test_resolve_foreach_items_from_params_yaml(tmp_path):
    """Should resolve variables defined in params.yaml."""
    (tmp_path / "params.yaml").write_text("datasets:\n  - movielens\n  - lastfm\n")
    resolved = _resolve_foreach_items("${datasets}", tmp_path, {})
    assert resolved == ["movielens", "lastfm"]

def test_resolve_foreach_items_from_external_vars_file(tmp_path):
    """Should resolve variables defined in an external vars file referenced by dvc.yaml."""
    (tmp_path / "config.yaml").write_text("datasets:\n  - movielens\n  - lastfm\n")
    dvc_data = {
        "vars": ["config.yaml"]
    }
    resolved = _resolve_foreach_items("${datasets}", tmp_path, dvc_data)
    assert resolved == ["movielens", "lastfm"]

def test_resolve_foreach_items_unresolved_warning(tmp_path, capsys):
    """Should print a warning to stderr when resolving fails."""
    resolved = _resolve_foreach_items("${missing}", tmp_path, {})
    assert resolved == "${missing}"
    
    captured = capsys.readouterr()
    assert "⚠️ Warning: Could not resolve foreach items '${missing}'" in captured.err


def test_update_dvc_yaml_with_dynamic_foreach_script(tmp_path):
    """Should correctly resolve dynamic script paths in foreach loop and generate hashes."""
    from dvc_viewer.updater import update_dvc_yaml
    
    # Create the dynamic script files
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "download_movielens.py").write_text("print('movielens')")
    (tmp_path / "scripts" / "download_lastfm.py").write_text("print('lastfm')")
    
    # Create dvc.yaml
    dvc_content = {
        "vars": [
            {"datasets": ["movielens", "lastfm"]}
        ],
        "stages": {
            "download": {
                "foreach": "${datasets}",
                "do": {
                    "cmd": "python3 scripts/download_${item}.py",
                    "deps": [
                        "scripts/download_${item}.py"
                    ]
                }
            }
        }
    }
    with open(tmp_path / "dvc.yaml", "w") as f:
        yaml.dump(dvc_content, f)
        
    update_dvc_yaml(tmp_path)
    
    # Check that hashes were generated for each variant
    hash_dir = tmp_path / ".dvc-viewer" / "hashes"
    assert (hash_dir / "download@movielens.hash").exists()
    assert (hash_dir / "download@lastfm.hash").exists()
    
    # Read the hashes and check that they are correct hashes for the respective files
    hash_movielens = (hash_dir / "download@movielens.hash").read_text(encoding="utf-8")
    hash_lastfm = (hash_dir / "download@lastfm.hash").read_text(encoding="utf-8")
    assert hash_movielens != hash_lastfm  # they are different scripts, so hashes should differ!

