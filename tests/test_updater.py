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
