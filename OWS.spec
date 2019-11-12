# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['src\\crawlUI.py'],
             pathex=['D:\\Projects\\Crawler\\SpiderGUI'],
             binaries=[],
             datas=[('src\\settings.toml', '.'),
					('src\\style.css', '.'),
					('src\\modules', 'modules'),
					('src\\doc', 'doc')],
             hiddenimports=['validators', 'pandas', 'qtawesome'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='OWS',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Open Web Scraper')
