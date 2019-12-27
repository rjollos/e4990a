#!/usr/bin/env bash

eval "$(pyenv init -)" && pyenv shell e4990a
python -m e4990a "$@"
