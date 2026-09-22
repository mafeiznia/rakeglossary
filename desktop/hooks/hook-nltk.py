# Custom hook to override pyinstaller-hooks-contrib's default nltk hook.
# That hook auto-bundles the entire %APPDATA%\nltk_data directory.
# We bundle our own minimal NLTK data via the datas list in build.spec,
# so this hook intentionally does nothing.
datas = []
binaries = []
hiddenimports = []
