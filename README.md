# etelemetry-server
Server for application monitoring and usage statistics.

[Python API](https://github.com/mgxd/etelemetry-client)

## Installation

```
$ pip install https://github.com/mgxd/etelemetry-server/archive/master.zip
```

## Usage
### With docker-compose

```
docker-compose [-f /path/to/compose/file.yml] up
```

By default, will be listening to port `8000`.


### Local

To start the server:

```
$ et up [--host] [--port]
```

Ensure the mongodb daemon is up and runnning

```
$ service mongod status
...

# if it is not, start it
$ service mongod start
```

## Example Calls

```
# ensure server is running
$ curl https://rig.mit.edu/et/

{"hello":"world"}

# check project
$ curl https://rig.mit.edu/et/projects/mgxd/etelemetry-client

{"version":"0.1"}
```
