# Werkpin
> CLI tool, that leverages remote file read into full RCE through Werkzeug debug console

## Usage

The crucial part is providing an executable, that will read remote files. It should cat the bytes of the file, given its path.
It should work like `cat` command on the local machine.

```bash
# Your file read script should accept file as first argument:
$ ./leak_file_from_server.sh <filename>
# Then use it in script as follows:
$ werkpin.py  --leak ... -fr './leak_file_from_server.sh'
```

The program knows to execute it with different filenames as arguments during the calculataion process.

We do need some tweaking, though. We have to choose the right interface, modname, and appname.
Usually the latter two work by default.

## Help

```

Werkpin

  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -q, --quiet           Quiet mode
  -v, --verbose         Verbose mode
  -fr FILE_READER, --file-reader FILE_READER
                        Executable command to read file. e.g. './leak_remote.sh'
  -u URL, --url URL     URL to target, that ends in /console
  -U USERNAME, --username USERNAME
                        Username that allegedly runs the application. None implies inference from environ.
  -M MODNAME, --modname MODNAME
                        Module name that allegedly runs the application
  -A APPNAME, --appname APPNAME
                        Application name that allegedly runs the application
  -F APPFILE, --appfile APPFILE
                        Application file that allegedly runs the application
  -I IFACE, --running-interface IFACE
                        Interface that the application is running on
  -wv WERKZEUG_VERSION, --werkzeug-version WERKZEUG_VERSION
                        Werkzeug version. None implies inference from headers.
```

## TODOs :smile:
- [ ] Nicer CLI, interactive net iface selection
- [ ] Automatic persistance
- [ ] Better heuristics for parameters 

### Disclaimer
I do not endorse any illegal use of this tool. This tool is meant for educational purposes only. Use at your own risk.
