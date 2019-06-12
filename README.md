# etelemetry
*ET phone home*

### Installation

```
$ pip install https://github.com/mgxd/etelemetry/archive/master.zip
```

### Usage


###### With docker-compose

```
docker-compose up
```

By default, will be listening to port `8000`.

###### Local

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
