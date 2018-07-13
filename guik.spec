# -*- mode: python -*-

block_cipher = None


a = Analysis(['guik.py'],
             pathex=['C:\\Users\\jkroes\\Desktop\\MyProjects\\appk'],
             binaries=[],
             datas=[('help.gif', '.'), ('dprlogo_3.gif', '.'), ('Tables\\112017', 'Tables\\112017'), ('chloropicrin_products.csv', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='guik',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False)
