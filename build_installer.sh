#!/usr/bin/env sh

DISTNAME=mac
pyinstaller --clean \
	--distpath ./dist/$DISTNAME \
	--noconfirm \
	--onedir \
	--hidden-import='pyvisa_py' \
	--add-data=template.ini:. \
	e4990a.py

SCRIPTPATH=dist/e4990a
cat > $SCRIPTPATH <<EOF
#!/usr/bin/env sh
EXEPATH=$DISTNAME/e4990a/e4990a
chmod 755 "\$EXEPATH"
xattr -r -d com.apple.quarantine $DISTNAME
"./\$EXEPATH" "\$1"
EOF
chmod 755 $SCRIPTPATH
