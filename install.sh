#!/usr/bin/env bash

PYVER=3.9.1
VIRTUALENV=e4990a

brew install pyenv pyenv-virtualenv tcl-tk 2>/dev/null

# The Python version installed in pyenv must be built with tcl-tk
# support for MatPlotLib and shared lib support PyInstaller.
PYTHON_CONFIGURE_OPTS="\
--with-tcltk-includes='-I$(brew --prefix tcl-tk)/include' \
--with-tcltk-libs='-L$(brew --prefix tcl-tk)/lib -ltcl8.6 -ltk8.6' \
--enable-shared"

if [ -z $(pyenv versions --bare | grep "^$PYVER$") ]; then
  echo $PYTHON_CONFIGURE_OPTS
  env PYTHON_CONFIGURE_OPTS="$PYTHON_CONFIGURE_OPTS" pyenv install $PYVER
fi
if [ -z $(pyenv versions --bare | grep "^$VIRTUALENV$") ]; then
  pyenv virtualenv $PYVER $VIRTUALENV
fi
eval "$(pyenv init -)" && pyenv shell $VIRTUALENV

pip install -U pip setuptools wheel
pip install -Ur requirements.txt
pip install -Ur requirements-dev.txt
python -m markdown -x extra README.md > README.html
