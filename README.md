# HLS Streaming Server

## Example
```
# Buid it
$ docker build .

# Run API
$ docker run --rm -i -p 8080:8080 -t -v $PWD:/site -w /site stream python3 -m stream

# Run Web UI
$ docker run --rm -i -p 8080:8080 -t -v $PWD:/site -w /site stream npm start
```