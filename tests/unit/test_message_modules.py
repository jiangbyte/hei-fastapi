""" Author: Charlie

message 模块仅保留公告 / 通知 / 反馈；IM 相关包不得再被发现。
"""
from __future__ import annotations

import ast
from pathlib import Path

from app.platform.module.discovery import clear_module_specs_cache, load_module_specs


def test_message_module_specs_exclude_im():
    clear_module_specs_cache()
    names = {spec.name for spec in load_module_specs(include_disabled=True)}
    assert "message.announcement" in names
    assert "message.notification" in names
    assert "message.feedback" in names
    for forbidden in (
        "message.im",
        "message.friend",
        "message.group",
        "message.conversation",
        "message.message",
        "message.offline",
        "message.terminal",
    ):
        assert forbidden not in names


def test_notification_service_has_no_im_import():
    path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "modules"
        / "message"
        / "notification"
        / "service.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "message.im" not in node.module
            assert not node.module.endswith(".im")
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "message.im" not in alias.name
