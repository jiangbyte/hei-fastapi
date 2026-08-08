""" Author: Charlie """

from app.platform.module.paths import (
    DEFAULT_FILES_PUBLIC_PATH,
    api_version_glob_prefix,
)


def test_files_public_path_matches_v1_convention():
    assert DEFAULT_FILES_PUBLIC_PATH == "/api/v1/files"


def test_version_glob_for_whitelist():
    assert api_version_glob_prefix() == "/api/v*"
