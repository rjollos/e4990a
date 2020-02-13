#!/usr/bin/env bash

PYVER=3.8.1
VIRTUALENV=e4990a

brew install pyenv pyenv-virtualenv tcl-tk 2>/dev/null

PYTHON_CONFIGURE_OPTS="\
--with-tcltk-includes='-I$(brew --prefix tcl-tk)/include' \
--with-tcltk-libs='-L$(brew --prefix tcl-tk)/lib -ltcl8.6 -ltk8.6'"

if [ -z $(pyenv versions --bare | grep "^$PYVER$") ]; then
  pyenv install $PYVER
fi
if [ -z $(pyenv versions --bare | grep "^$VIRTUALENV$") ]; then
  pyenv virtualenv $PYVER $VIRTUALENV
fi
eval "$(pyenv init -)" && pyenv shell $VIRTUALENV

pip install -U pip wheel
pip install -r requirements.txt
python -m markdown -x gfm README.md > README.html
