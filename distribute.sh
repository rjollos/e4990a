#!/usr/bin/env sh

name=e4990a-$(date +'%Y%m%dT%H%M%S')-macos.zip
zip -j $name \
	dist/e4990a \
	README.html \
	read_e4990a_data.m \
	plot_impedance.m
echo "Created $name"
