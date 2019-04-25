# etelemetry
*ET phone home*

### Installation

```
$ pip install https://github.com/mgxd/etelemetry/archive/master.zip
```

### Usage

To start the server:

```
$ et [--host] [--port] up
```

Ensure the mongodb daemon is up and runnning

```
$ service mongod status
...
# if it is not, start it (requires sudo)
$ service mongod start
```
