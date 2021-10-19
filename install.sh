#!/usr/bin/env bash

PYVER=3.9.7
VIRTUALENV=e4990a

if ! command -v brew &> /dev/null
then
  echo "Please install Homebrew: https://brew.sh"
  exit 1
fi
if ! brew list pyenv &> /dev/null ||
   ! brew list pyenv-virtualenv &> /dev/null
then
  echo "Please install pyenv and pyenv-virtualenv using Homebrew:"
  echo "$ brew install pyenv pyenv-virtualenv"
  exit 1
fi
# The Python version installed in pyenv must be built with
# shared lib support PyInstaller.
PYTHON_CONFIGURE_OPTS="--enable-shared"

if [ -z $(pyenv versions --bare | grep "^$PYVER$") ]; then
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
