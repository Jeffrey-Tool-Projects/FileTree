"""Every text the window shows, one module per language (see ``je_file_tree.gui.i18n``)."""

from __future__ import annotations

from je_file_tree.gui.strings.en import EN
from je_file_tree.gui.strings.ja import JA
from je_file_tree.gui.strings.ko import KO
from je_file_tree.gui.strings.zh_cn import ZH_CN
from je_file_tree.gui.strings.zh_tw import ZH_TW

STRINGS: dict[str, dict[str, str]] = {"en": EN, "zh-TW": ZH_TW, "zh-CN": ZH_CN, "ja": JA, "ko": KO}
