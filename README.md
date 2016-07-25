## P1 > Graphite

Python program to read DSMR telegrams from a serial port connected to
the P1 port of a smart meter, and send the resulting data to Graphite.

Inspired by and based on https://github.com/jvhaarst/DSMR-P1-telegram-reader.

### Work in progress

This project is pretty much in a state of flux.
Expect things to change.

### Usage

Place `p1graphite.py` somewhere in your filesystem. Install the
[`supervisor`](http://supervisord.org/) package.

Create a file `/etc/supervisor/conf.d/p1graphite.conf` with the
following contents:

```
[program:p1graphite]
command = /usr/bin/python /path/where/you/put/p1graphite.py --prefix myhome
stdout_logfile = /var/log/p1graphite-stdout.log
stdout_logfile_maxbytes = 10MB
stdout_logfile_backups = 5
stderr_logfile = /var/log/p1graphite-stderr.log
stderr_logfile_maxbytes = 10MB
stderr_logfile_backups = 5
```

You may change `/path/to/...` and `myhome` to your liking.

Now let supervisor start the script. See supervisor's manual for that.

The script has a number of command line options that you may find
useful:

```
  -h, --help            show this help message and exit
  -d, --debug           Debug mode
  -p PORT, --port PORT  Serial port
  -b BAUDRATE, --baudrate BAUDRATE
                        Serial port baudrate
  -H HOST, --host HOST  Graphite host
  -g GPORT, --gport GPORT
                        Graphite port
  --prefix PREFIX       Graphite prefix
```
