# This constructs a windows installer for this version of twarc, using pynsist
# It assumes that nsis is present on the system, and that a Python interpreter
# and Pip are present

sudo apt install nsis

pip install pynsist

# First we're going to setup dependencies by downloading wheels
# There's also a way to specify this in the nsis script, but this is more
# explicit, and necessary for the one dependency that doesn't have a wheel
# anyway.

mkdir wheels

# configobj doesn't have a wheel available, so we'll make a local one.
pip wheel configobj --no-deps -w wheels

# get wheels for everything else, ignoring the one wheel already present
pip download -r requirements.txt -d wheels --platform win_amd64 --platform any --only-binary=:all: -f wheels/

pynsist installer.cfg





