#!/usr/bin/env sh

name=e4990a-$(date +'%Y%m%dT%H%M%S')-macos.zip
chmod 755 dist/e4990a
cp README.html dist/
cp read_e4990a_data.m dist/
cp plot_impedance.m dist/
zip -j $name dist/*
echo "Created $name"
