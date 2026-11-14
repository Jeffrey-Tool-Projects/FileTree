"""The drive overview records used space on its worker and shows a forecast column in every language."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QByteArray, QSettings, Qt

from test_gui import _wait
from je_file_tree.core.forecast import DAY, ForecastStore, Sample
from je_file_tree.core.trash_size import TrashUsage
from je_file_tree.gui import forecast as forecast_view
from je_file_tree.gui import i18n, volumes
from je_file_tree.gui.i18n import tr

GIB = 1024 ** 3
NOW = 1_800_000_000.0
KEY = "D:/\x1fowned\x1fntfs"
COLUMN = 9


def _storage(*, free: int = 60 * GIB, total: int = 100 * GIB):
    return SimpleNamespace(refresh=lambda: None, isValid=lambda: True, isReady=lambda: True,
                           rootPath=lambda: "D:/", displayName=lambda: "owned drive",
                           device=lambda: QByteArray(b"owned"), fileSystemType=lambda: QByteArray(b"ntfs"),
                           bytesTotal=lambda: total, bytesFree=lambda: free, bytesAvailable=lambda: free)


@pytest.fixture
def sources(monkeypatch):
    storages = [_storage()]
    monkeypatch.setattr(volumes.QStorageInfo, "mountedVolumes", lambda: storages)
    monkeypatch.setattr(volumes, "trash_usage", lambda *_args, **_kwargs: TrashUsage(0, 0, True))
    monkeypatch.setattr(volumes, "allocation_unit", lambda _root: 4096)
    return storages


@pytest.fixture
def settings(tmp_path: Path) -> QSettings:
    return QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)


@pytest.fixture
def language():
    yield i18n.set_language
    i18n.set_language("en")


def _history(path: Path, days: int = 10, per_day: int = GIB) -> ForecastStore:
    """Daily samples up to a day before NOW, growing ``per_day`` towards the 40 GiB the fake drive now uses."""
    filler = ForecastStore(path, min_interval=0)
    filler.record((KEY, Sample(NOW - (days - index) * DAY, 40 * GIB - (days - index) * per_day, 100 * GIB))
                  for index in range(days))
    return ForecastStore(path)


def _open(qapp, settings, store=None, rows=1):
    dialog = volumes.VolumesDialog("auto", settings=settings, store=store, clock=lambda: NOW)
    _wait(qapp, lambda: dialog.model.rowCount() == rows)
    return dialog


@pytest.mark.parametrize("code", list(i18n.LANGUAGES))
def test_growing_drive_shows_rate_date_and_tooltip_in_every_language(qapp, sources, settings, tmp_path, language,
                                                                     code):
    language(code)
    store = _history(tmp_path / "forecast.json")
    dialog = _open(qapp, settings, store)
    try:
        index = dialog.model.index(0, COLUMN)
        row = dialog.model.row_at(0)
        assert row.forecast is not None and row.forecast.samples == 11
        assert row.forecast.bytes_per_day == pytest.approx(GIB, rel=0.01)
        expected_date = datetime.fromtimestamp(row.forecast.full_at).strftime("%Y-%m-%d")
        assert index.data() == tr("forecast_growing", rate="1.0 GB", date=expected_date)
        assert expected_date == datetime.fromtimestamp(NOW + 60 * DAY).strftime("%Y-%m-%d")
        tooltip = index.data(Qt.ItemDataRole.ToolTipRole)
        assert "11" in tooltip and "10.0" in tooltip and tooltip == forecast_view.forecast_tooltip(row.forecast,
                                                                                                    recording=True)
        assert dialog.model.headerData(COLUMN, Qt.Orientation.Horizontal) == tr("forecast_column")
        assert dialog.record.text() == tr("forecast_record")
        if code != "en":
            assert tr("forecast_growing", rate="x", date="y") != i18n.STRINGS["en"]["forecast_growing"].format(
                rate="x", date="y")
        assert len(row.trend) == 11 and row.trend[-1] == pytest.approx(0.4)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
        dialog.show()
        qapp.processEvents()
        assert not dialog.grab().isNull()
    finally:
        dialog.reject()
        dialog.deleteLater()


def test_a_new_drive_has_not_enough_history_and_records_one_sample(qapp, sources, settings, tmp_path):
    store = ForecastStore(tmp_path / "forecast.json")
    dialog = _open(qapp, settings, store)
    try:
        assert dialog.model.index(0, COLUMN).data() == tr("forecast_not_enough")
        assert "1" in dialog.model.index(0, COLUMN).data(Qt.ItemDataRole.ToolTipRole)
        assert store.load()[0][KEY] == (Sample(NOW, 40 * GIB, 100 * GIB),)
    finally:
        dialog.reject()
        dialog.deleteLater()


def test_a_shrinking_drive_is_not_growing_and_unknown_usage_is_not_recorded(qapp, sources, settings, tmp_path):
    store = _history(tmp_path / "forecast.json", per_day=-GIB)
    sources.append(SimpleNamespace(**{**vars(_storage(free=-1)), "rootPath": lambda: "E:/"}))
    dialog = _open(qapp, settings, store, rows=2)
    try:
        texts = {dialog.model.row_at(row).root: dialog.model.index(row, COLUMN).data() for row in range(2)}
        assert texts == {"D:/": tr("forecast_stable"), "E:/": tr("forecast_unknown")}
        assert list(store.load()[0]) == [KEY]
    finally:
        dialog.reject()
        dialog.deleteLater()


def test_recording_off_writes_nothing_and_turning_it_on_records(qapp, sources, settings, tmp_path):
    settings.setValue(forecast_view.SETTING, False)
    store = ForecastStore(tmp_path / "forecast.json")
    dialog = _open(qapp, settings, store)
    try:
        assert not dialog.record.isChecked()
        assert dialog.model.index(0, COLUMN).data() == tr("forecast_off")
        assert dialog.model.index(0, COLUMN).data(Qt.ItemDataRole.ToolTipRole) == tr("forecast_off_tip")
        assert not store.path.exists()
        worker = dialog.worker
        dialog.record.setChecked(True)
        assert forecast_view.recording_enabled(settings)
        _wait(qapp, lambda: dialog.worker is not worker and not dialog.worker.isRunning()
              and dialog.model.row_at(0) is not None and dialog.model.row_at(0).forecast is not None)
        assert dialog.model.index(0, COLUMN).data() == tr("forecast_not_enough")
        assert KEY in store.load()[0]
        dialog.record.setChecked(False)
        assert settings.value(forecast_view.SETTING) in (False, "false")
    finally:
        dialog.reject()
        dialog.deleteLater()


def test_a_failed_save_is_shown_and_the_forecast_still_appears(qapp, sources, settings, tmp_path):
    (tmp_path / "blocked").write_text("not a folder", encoding="utf-8")
    dialog = _open(qapp, settings, ForecastStore(tmp_path / "blocked" / "forecast.json"))
    try:
        assert tr("forecast_save_failed", reason="") in dialog.status.text()
        assert dialog.model.index(0, COLUMN).data() == tr("forecast_not_enough")
    finally:
        dialog.reject()
        dialog.deleteLater()


def test_default_store_uses_the_redirected_application_data_file(qapp, sources, settings, tmp_path):
    dialog = _open(qapp, settings)
    try:
        assert (tmp_path / "forecast" / "volumes.json").is_file()
    finally:
        dialog.reject()
        dialog.deleteLater()


def test_no_data_location_is_explained(qapp, sources, settings, monkeypatch):
    monkeypatch.setattr(forecast_view, "forecast_file", lambda: None)
    dialog = _open(qapp, settings)
    try:
        assert tr("forecast_unavailable") in dialog.status.text()
    finally:
        dialog.reject()
        dialog.deleteLater()


def test_texts_for_far_and_unknown_forecasts():
    from je_file_tree.core.forecast import Forecast, ForecastState

    far = Forecast(ForecastState.GROWING, 2 * 1024 * 1024, None, 9, 4.0)
    assert forecast_view.forecast_text(far, "auto", recording=True) == tr("forecast_not_soon", rate="2.0 MB",
                                                                          years="5")
    assert forecast_view.forecast_text(None, "auto", recording=True) == tr("forecast_unknown")
    assert forecast_view.sort_value(None) > forecast_view.sort_value(far) > NOW
    assert "3" in forecast_view.record_tip() and "400" in forecast_view.record_tip()


def test_sparkline_draws_the_used_share_before_the_text(qapp):
    from PySide6.QtCore import QRect
    from PySide6.QtGui import QColor, QImage, QPainter
    from PySide6.QtWidgets import QStyleOptionViewItem

    model = volumes.VolumesModel()
    model.set_rows([volumes.Volume("D:/", "owned", "NTFS", 1000, 600, 300, 4096, TrashUsage(0, 0, True),
                                   None, (0.1, 0.4, 0.2, 0.6))])
    image = QImage(330, 30, QImage.Format.Format_ARGB32)
    image.fill(QColor("white"))
    option = QStyleOptionViewItem()
    option.rect = QRect(0, 0, 330, 30)
    painter = QPainter(image)
    try:
        forecast_view.SparklineDelegate().paint(painter, option, model.index(0, COLUMN))
    finally:
        painter.end()
    drawn = sum(image.pixelColor(x, y) != QColor("white") for x in range(4, 60) for y in range(30))
    assert drawn > 20
    assert option.text == ""


def test_the_recycle_bin_dialog_neither_records_nor_shows_a_forecast(qapp, sources, tmp_path):
    from je_file_tree.gui.bin_dialog import BinDialog

    dialog = BinDialog("auto")
    try:
        _wait(qapp, lambda: dialog.model.rowCount() == 1)
        assert dialog.view.isColumnHidden(COLUMN) and dialog.record.isHidden()
        assert dialog.model.row_at(0).forecast is None
        assert not (tmp_path / "forecast").exists()
    finally:
        dialog.reject()
        dialog.deleteLater()
