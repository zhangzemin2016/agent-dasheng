# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('theme', 'theme'), ('components', 'components'), ('views', 'views'), ('core', 'core'), ('tools', 'tools'), ('controllers', 'controllers'), ('services', 'services'), ('utils', 'utils')],
    hiddenimports=['langchain', 'langchain_openai', 'langchain_deepseek', 'yaml', 'aiohttp', 'dotenv', 'tree_sitter', 'tree_sitter_python'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AI Agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.png'],
)
