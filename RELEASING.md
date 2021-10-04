# Releasing

New versions of twarc can be released by creating a release and assigning a new tag in the GitHub repo. The release, including upload of the new version to PyPI, is performed by GitHub actions when a new tag is created, using the PyPI token stored in the secrets associated with the repository. Anybody who has the permission to create a tag can perform a release.

Steps in a release:

1. Update the version number in `twarc/version.py` - the format is MAJOR.MINOR.PATCH and should always be increasing and unique.
2. Make a new release from https://github.com/DocNow/twarc/releases (hit the 'draft new release' button on the top right).
3. Create a new tag, matching the version number in `twarc/version.py`, with a v prefix (ie. vMAJOR.MINOR.PATCH)
4. Write release notes.
5. Publish the release.
6. Make sure the GitHub action completes successfully.
7. Double check that the new version correctly installs from PyPI: `pip install --upgrade twarc` should install the new version created above.
