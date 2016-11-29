from PyInstaller.compat import is_py2
if is_py2:
    hiddenimports = ['HTMLParser']
else:
    hiddenimports = ['html.parser']
