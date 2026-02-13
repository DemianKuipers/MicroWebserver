# MicroWebserver

[MicroWebserver](https://github.com/DemianKuipers/MicroWebserver) is a lightweight HTTP server for MicroPython.
It supports code defined handlers and simple file serving.

## Installation

You can download the files and copy them to your development folder. You can use an IDE like [Thonny](https://thonny.org) to upload them to your Raspberry Pi Pico W or ESP board.

## Using the webserver

As a quick start you can add these lines to your code:

```python
import Http

server = Http.Server()
# Define handlers here
# Enable wifi here
server.start()

# Main loop
while True:
  server.checkRequest()
```


