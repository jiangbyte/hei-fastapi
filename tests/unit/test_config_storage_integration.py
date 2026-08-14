""" Author: Charlie """

from pathlib import Path

import pytest

from app.core.config.enums import StorageProvider
from app.core.storage import manager as storage_manager
from app.core.storage.config import StorageConfig


@pytest.fixture(autouse=True)
def clear_storage_manager_cache():
    storage_manager.clear_storage_cache()
    yield
    storage_manager.clear_storage_cache()


def _local_config(config_id: str, root: Path, *, is_default: bool = False) -> StorageConfig:
    return StorageConfig(
        id=config_id,
        name=config_id,
        provider=StorageProvider.LOCAL,
        local_root=str(root),
        public_path=f"/files/{config_id}",
        is_default=is_default,
    )


def test_resolve_storage_config_uses_snapshot_config_id_and_provider(monkeypatch, tmp_path):
    default_config = _local_config("local-default", tmp_path / "default", is_default=True)
    archive_config = _local_config("local-archive", tmp_path / "archive")
    monkeypatch.setattr(
        storage_manager.config_reader,
        "_storage_configs",
        {
            default_config.id: default_config,
            archive_config.id: archive_config,
        },
    )
    monkeypatch.setattr(storage_manager.config_reader, "_default_storage_id", default_config.id)
    monkeypatch.setattr(storage_manager.config_reader, "_version", 100)

    assert storage_manager.resolve_storage_config("local-archive") == archive_config
    assert storage_manager.resolve_storage_config(provider=StorageProvider.LOCAL) == default_config

    from urllib.parse import urlparse

    storage = storage_manager.get_storage("local-archive", allow_settings_fallback=False)
    assert storage.root == (tmp_path / "archive").resolve()
    url = storage.get_object_url("a/b.txt")
    parsed = urlparse(url)
    assert parsed.path == "/files/local-archive/a/b.txt"
    assert not parsed.query


def test_storage_cache_is_versioned_by_config_snapshot(monkeypatch, tmp_path):
    first_config = _local_config("local-default", tmp_path / "v1", is_default=True)
    monkeypatch.setattr(
        storage_manager.config_reader,
        "_storage_configs",
        {first_config.id: first_config},
    )
    monkeypatch.setattr(storage_manager.config_reader, "_default_storage_id", first_config.id)
    monkeypatch.setattr(storage_manager.config_reader, "_version", 1)

    first_storage = storage_manager.get_storage(allow_settings_fallback=False)

    second_config = _local_config("local-default", tmp_path / "v2", is_default=True)
    monkeypatch.setattr(
        storage_manager.config_reader,
        "_storage_configs",
        {second_config.id: second_config},
    )
    monkeypatch.setattr(storage_manager.config_reader, "_version", 2)

    second_storage = storage_manager.get_storage(allow_settings_fallback=False)
    assert second_storage is not first_storage
    assert second_storage.root == (tmp_path / "v2").resolve()


def test_explicit_unknown_storage_config_id_does_not_fallback(monkeypatch):
    monkeypatch.setattr(storage_manager.config_reader, "_storage_configs", {})
    monkeypatch.setattr(storage_manager.config_reader, "_default_storage_id", None)

    with pytest.raises(RuntimeError, match="Storage config is not available"):
        storage_manager.resolve_storage_config("missing-storage")


def test_config_value_type_coerced():
    from app.core.config.coerce import coerce_config_value

    assert coerce_config_value("false", bool) is False
    assert coerce_config_value("42", int) == 42
    assert coerce_config_value("2.5", float) == 2.5
    assert coerce_config_value('["a", "b"]', list[str]) == ["a", "b"]
    assert coerce_config_value("not-an-int", int) is None
    assert coerce_config_value("true", bool | None) is True
    assert coerce_config_value(None, int) is None
