@echo off

set NAME=e4990a-%date:~10,4%%date:~4,2%%date:~7,2%T%time:~0,2%%time:~3,2%%time:~6,2%-win64.zip
copy README.html dist\
copy read_e4990a_data.m dist\
copy plot_impedance.m dist\
zip -j %NAME% dist\*
echo "Created %NAME%"
