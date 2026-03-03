# -*- mode: python ; coding: utf-8 -*-
"""Bunseki PyInstaller spec ファイル。

ビルド方法:
    pip install pyinstaller
    pyinstaller bunseki.spec

生成先: dist/Bunseki/
"""
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # matplotlib QtAgg バックエンド
        "matplotlib.backends.backend_qtagg",
        # PySide6 プラグイン
        "PySide6.QtSvg",
        "PySide6.QtSvgWidgets",
        # pandas / openpyxl
        "openpyxl",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 不要なバックエンドを除外してサイズ削減
        "tkinter",
        "matplotlib.backends.backend_tk",
        "matplotlib.backends.backend_tkagg",
        "PyQt5",
        "PyQt6",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Bunseki",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI アプリのためコンソール非表示
    icon=None,      # アイコンを設定する場合: icon="resources/assets/app-logo.ico"
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Bunseki",
)
