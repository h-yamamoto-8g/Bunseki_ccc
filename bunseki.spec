# -*- mode: python ; coding: utf-8 -*-
"""Bunseki PyInstaller spec ファイル。

ビルド方法:
    pip install pyinstaller
    pyinstaller bunseki.spec

生成先: dist/Bunseki.exe  (単一ファイル)
"""
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[("resources/assets/splash.png", "resources/assets")],
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

# PyInstaller Splash: Tcl/Tk ベースで Python インポート前に即座に表示
splash = Splash(
    "resources/assets/splash.png",
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,          # テキスト表示なし
    text_color="white",
)

exe = EXE(
    pyz,
    splash,                 # Splash ターゲット
    splash.binaries,        # Tcl/Tk バイナリ
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Bunseki",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI アプリのためコンソール非表示
    icon="resources/assets/app-logo.ico",
)
