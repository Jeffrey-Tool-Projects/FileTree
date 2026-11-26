"""Previews are bounded, read only unchanged local files, and stay off until asked for."""

import os
import threading
import zipfile

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QImage

from test_gui import _wait, window as window  # noqa: PLC0414 - explicit pytest fixture re-export
from je_file_tree.core import preview as module
from je_file_tree.core.archives import zip_members
from je_file_tree.core.node import Node
from je_file_tree.core.preview import ARCHIVE, BINARY, IMAGE, TEXT, PreviewError, decode, read_preview, suffix_of
from je_file_tree.core.scanner import scan
from je_file_tree.core.snapshot import pack_snapshot, unpack_snapshot
from je_file_tree.gui import i18n, preview_pane
from je_file_tree.gui.preview_pane import PREVIEW_KEY, PreviewPane, decode_picture

_READERS = {".zip": zip_members}


def _node(path) -> Node:
    return next(node for node in scan(path.parent).root.children if node.name == path.name)


def _picture(path, width=900, height=600) -> None:
    image = QImage(width, height, QImage.Format.Format_RGB32)
    image.fill(QColor("#2a78b8"))
    assert image.save(str(path))


@pytest.mark.parametrize("name, suffix", [("a.TXT", ".txt"), ("a.tar.GZ", ".gz"), ("noext", ""), (".hidden", ""),
                                          ("..", ""), ("dot.", "")])
def test_suffixes(name, suffix):
    assert suffix_of(name) == suffix


@pytest.mark.parametrize("data, text", [
    (b"", ""), ("檔案\n二".encode(), "檔案\n二"), (b"\xef\xbb\xbfbom", "bom"), ("標".encode("utf-16"), "標"),
    (b"\xff\xfe", ""), (b"tab\tline\r\n", "tab\tline\r\n"), (b"\x00\x01\x02\x03", None), (b"\x80\x81\xfe", None),
    (b"MZ\x90\x00" * 50, None),
])
def test_text_is_utf8_or_marked_utf16(data, text):
    assert decode(data, whole=True) == text


def test_a_character_cut_by_the_limit_is_still_text():
    data = "檔".encode() * 10
    assert decode(data[:-1], whole=False) == "檔" * 9 and decode(data[:-1], whole=True) is None


def test_texts_are_cut_by_bytes_lines_and_width(tmp_path):
    small, big, long = tmp_path / "small.log", tmp_path / "big.log", tmp_path / "long.json"
    small.write_text("one\ntwo", encoding="utf-8")
    big.write_text("line\n" * 100_000, encoding="utf-8")
    long.write_text("x" * 5000, encoding="utf-8")
    assert read_preview(_node(small), _READERS) == module.Preview(TEXT, text="one\ntwo")
    preview = read_preview(_node(big), _READERS)
    assert preview.more and len(preview.text.splitlines()) == module.MAX_LINES
    preview = read_preview(_node(long), _READERS)
    assert preview.more and len(preview.text) == module.MAX_LINE


def test_binary_files_and_large_pictures_show_nothing(tmp_path, monkeypatch):
    program = tmp_path / "tool.exe"
    program.write_bytes(b"MZ\x00\x01" * 100)
    assert read_preview(_node(program), _READERS).kind == BINARY
    picture = tmp_path / "big.png"
    picture.write_bytes(b"x" * 2000)
    monkeypatch.setattr(module, "MAX_IMAGE_BYTES", 1000)
    with pytest.raises(PreviewError):
        read_preview(_node(picture), _READERS)


def test_archives_list_their_directory_without_extracting(tmp_path, monkeypatch):
    archive = tmp_path / "pack.zip"
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr("folder/a.txt", "x" * 10)
        stream.writestr("b.txt", "y" * 5)
    monkeypatch.setattr(zipfile.ZipFile, "open", lambda *_args, **_kwargs: pytest.fail("members are never opened"))
    preview = read_preview(_node(archive), _READERS)
    assert preview.kind == ARCHIVE and not preview.more
    assert dict(preview.lines) == {"folder/": 10, "folder/a.txt": 10, "b.txt": 5}
    monkeypatch.setattr(module, "MAX_MEMBERS", 1)
    assert read_preview(_node(archive), _READERS).more


@pytest.mark.parametrize("change", ["content", "gone", "folder"])
def test_files_that_changed_since_the_scan_are_refused(tmp_path, change):
    path = tmp_path / "a.txt"
    path.write_text("old", encoding="utf-8")
    node = _node(path)
    path.unlink()
    if change == "content":
        path.write_text("something else", encoding="utf-8")
    elif change == "folder":
        path.mkdir()
    with pytest.raises(OSError):
        read_preview(node, _READERS)


def test_files_kept_only_online_are_never_opened(tmp_path, monkeypatch):
    path = tmp_path / "cloud.txt"
    path.write_text("local", encoding="utf-8")
    node = _node(path)
    from types import SimpleNamespace
    info = unpack_snapshot(node.snapshot)
    fields = dict(st_dev=info.device, st_ino=info.inode, st_size=info.size, st_mode=info.mode, st_nlink=info.links,
                  st_mtime_ns=info.modified_ns, st_ctime_ns=info.changed_ns, st_file_attributes=0x400000)
    recall = pack_snapshot(SimpleNamespace(**fields))
    node.snapshot = recall
    monkeypatch.setattr("je_file_tree.core.archives.stat_snapshot", lambda _path: recall)
    monkeypatch.setattr(os, "open", lambda *_args, **_kwargs: pytest.fail("opening would download it"))
    with pytest.raises(OSError):
        read_preview(node, _READERS)


def test_pictures_are_decoded_small(qapp, tmp_path):
    path = tmp_path / "a.png"
    _picture(path)
    image = decode_picture(path.read_bytes())
    assert (image.width(), image.height()) == (450, 300)
    for data in (b"", b"not a picture", path.read_bytes()[:60]):
        with pytest.raises(PreviewError):
            decode_picture(data)


@pytest.fixture
def pane(qapp, tmp_path):
    settings = QSettings(str(tmp_path / "preview.ini"), QSettings.Format.IniFormat)
    made = PreviewPane(settings)
    yield made
    made.stop(wait=True)
    made.deleteLater()


def test_nothing_is_read_until_it_is_turned_on(pane, qapp, tmp_path):
    path = tmp_path / "a.txt"
    path.write_text("hello", encoding="utf-8")
    pane.set_node(_node(path), active=True)
    assert not pane.enabled.isChecked() and not pane._timer.isActive() and not pane._running
    pane.enabled.setChecked(True)
    _wait(qapp, lambda: pane._preview is not None)
    assert pane.text.toPlainText() == "hello" and pane.status.text() == i18n.tr("preview_whole")
    assert pane._settings.value(PREVIEW_KEY, type=bool)
    pane.enabled.setChecked(False)
    assert pane.text.isHidden() and pane.text.toPlainText() == "" and not pane._timer.isActive()


def test_the_pane_shows_pictures_archives_and_failures(pane, qapp, tmp_path):
    picture, archive, broken = tmp_path / "a.png", tmp_path / "b.zip", tmp_path / "c.png"
    _picture(picture)
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr("inside.txt", "x")
    broken.write_bytes(b"no picture")
    pane.enabled.setChecked(True)
    pane.set_node(_node(picture), active=True)
    _wait(qapp, lambda: pane._preview is not None)
    assert pane._preview.kind == IMAGE and not pane.picture.isHidden() and pane.picture.pixmap().width() == 450
    pane.set_node(_node(archive), active=True)
    _wait(qapp, lambda: pane._preview is not None)
    assert "inside.txt" in pane.text.toPlainText() and pane.picture.isHidden()
    pane.set_node(_node(broken), active=True)
    _wait(qapp, lambda: pane.status.text() == i18n.tr("preview_failed"))
    assert pane.text.isHidden() and pane.picture.isHidden()


def test_folders_links_errors_and_inactive_panes_read_nothing(pane, tmp_path):
    pane.enabled.setChecked(True)
    file = Node(str(tmp_path / "x.txt"), False, size=1)
    for node, active in ((Node("folder", True, children=[]), True), (Node("l", False, is_link=True), True),
                         (None, True),
                         (Node("e", False, error="denied"), True), (file, True), (file, False)):
        pane.set_node(node, active=active)
        assert not pane._timer.isActive() and not pane._running


def test_a_newer_selection_discards_the_older_reply(pane, qapp, tmp_path, monkeypatch):
    for name in ("a.txt", "b.txt"):
        (tmp_path / name).write_text(name, encoding="utf-8")
    gate = threading.Event()
    real = preview_pane.read_preview

    def slow(node, readers, cancel):
        if node.name.endswith("a.txt"):
            gate.wait(5)
        return real(node, readers, cancel)
    monkeypatch.setattr(preview_pane, "read_preview", slow)
    pane.enabled.setChecked(True)
    pane.set_node(_node(tmp_path / "a.txt"), active=True)
    _wait(qapp, lambda: pane._running)
    pane.set_node(_node(tmp_path / "b.txt"), active=True)
    _wait(qapp, lambda: pane._preview is not None)
    gate.set()
    _wait(qapp, lambda: not pane._running)
    assert pane.text.toPlainText() == "b.txt"


def test_details_hosts_it_and_closing_joins_it(window, qapp, sample_tree):
    from je_file_tree.gui.scan_worker import analyse
    details = window.results.details
    window.results.show_outcome(analyse(scan(sample_tree)))
    assert details.body.maximumHeight() == 235
    details.toggle.setChecked(True)
    details.preview.enabled.setChecked(True)
    assert details.body.maximumHeight() > 235
    file = next(node for node in window.results.tree_model.root.iter_files() if node.size)
    details.set_node(file)
    _wait(qapp, lambda: details.preview._preview is not None)
    details.set_node(file, live=True)
    assert details.preview._preview is None and not details.preview._timer.isActive()
    details.stop(wait=True)
    assert not any(worker.isRunning() for worker in details.preview._running)
    details.preview.enabled.setChecked(False)
