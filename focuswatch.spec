# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['focuswatch/__main__.py'],
             pathex=['.'],
             binaries=[],
             datas=[
                 ('logging.json', '.'),
                 ('icon.png', '.'),
                 ('focuswatch', 'focuswatch'),
                 ('resources/icons/*.png', 'resources/icons'),
                 ('resources/styles/*.qss', 'resources/styles'),
                 ('resources/styles/components/*.qss', 'resources/styles/components'),
                 ('resources/styles/dialogs/*.qss', 'resources/styles/dialogs')
             ],
             hiddenimports=['PySide6.QtXml', 'PySide6.QtSvg'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='focuswatch',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None)