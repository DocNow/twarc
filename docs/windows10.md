# twarc2 on Windows 10

This guide assumes you already have a Twitter Developer Account, a registered App with your keys and a Bearer Token, and Python installed on Windows.

## Prerequisites and Installation

You must have Python installed and working on Windows.

Python will be located in different places on your computer if you installed Python from either the official website or from the Microsoft App store.

Check that you can run these successfully:

Open the command line `cmd.exe` or `PowerShell` or `Windows Terminal Preview` and run:

`python --version`

and

`pip --version`

If both give you some version output without errors everything is ready to go. Otherwise, install and configure `python` and `pip`.

`twarc2` CLI works best through [Windows Terminal Preview](https://www.microsoft.com/en-us/p/windows-terminal-preview/9n8g5rfz9xk3?activetab=pivot:overviewtab)

## Setting up twarc2

Install `twarc2` with

`pip install --upgrade twarc`

If you get a warning like 

```
WARNING: The scripts twarc.exe and twarc2.exe are installed in 'C:\Users\t495\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0\LocalCache\local-packages\Python39\Scripts' which is not on PATH.
  Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
```

You will need to add that folder to the PATH.

This will be different for your machine, so make sure to copy the full folder location from the command prompt, without the `'` quotes with `CTRL+C`.

Make sure that folder is set in PATH System Variables:

In Settings, find "edit the system environment variables"

After clicking on "Environment Variables"

Edit the "Path" variable in User Variables and add a new entry, in my case it was `C:\Users\t495\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0\LocalCache\local-packages\Python39\Scripts` but for you it will be different. Copy this from the warning it gives you, because it varies.

You should now be able to run `twarc2` from the command line:

`twarc2`

If you can see the instructions, everything is ready to go.

In powershell or command prompt, run:

`twarc2 configure`

When this is completed, twarc2 is ready to use.

## Escaping `"` Characters in Windows

The query you specify to search can contain `"` quotes for phrases, spaces and other special characters like `:` and `()`. When entered directly into the prompt these can be interpreted as part of the command, not part of the command line argument value. Windows has an odd way of escaping characters in the command line.

To use a `"` in a query, change it to `""` in Windows. The more common escape `\"` does not work.

For example, if you want to search for tweets that contain the phrase `"live laugh love"` or `"home sweet home"` in english, from the US, the query would be:

```
lang:en ("live laugh love" OR "home sweet home") place_country:US
```

Changing the `"` to `""` The twarc2 command for this would be:

```
twarc2 --archive "lang:en (""live laugh love"" OR ""home sweet home"") place_country:US" output.json
```

This Stackoverflow answer has the long version that explains why this works: https://stackoverflow.com/a/15262019

## Output Format Errors:

If you see this kind of error, for example when using `twarc2 flatten`:

> ⚡ Expecting value: line 1 column 1 (char 0)

It means the file was incorrectly saved. There is an edge case in Windows when writing output, do not use `>` to redirect `stdout`. This alters how files are written, and adds a BOM (Byte Order Mark) that makes the files unreadable to twarc for later, eg: when using `twarc2 flatten`. To fix the file, edit it in a Hex editor to remove the first 2 bytes.

For example, this will give you a bad file with a BOM:

`twarc2 search --limit 100 "dogs" > dogs.json`

While this will give you a correctly written UTF8 file:

`twarc2 search --limit 100 "dogs" dogs.json`

Do not redirect stdout to a file in Windows, instead - specify the output file as a command line argument.
