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

## Adding routes/handlers

You can define handlers for specific url's bij adding a route. This is done by defining a decorated function:

```python
@server.route("GET", "/")
def root(request):
    return Http.HtmlResponse('This is the root page')
```
Here **server** is the name of your Http.Server instance, **GET** is the HTTP method and **/** is the url for which this route is defined. The function should accept one parameter which will be of the **Http.Request** type. This object provides information about the HTTP request. The function should return a **Http.Response** object (or a convenience subclass of Http.Response, like Http.HtmlResponse).

### The Request class
The Request class has a couple of properties you can use in your handler:
- **method**: The HTTP method used, most commonly GET, POST, PUT, DELETE
- **uri**: The HTTP request uri; this includes both the path and parameters
- **path**: The path part of the request uri
- **params**: A dict that contains the uri parameters
- **headers**: A dict containing the HTTP headers
- **data**: Binary data send along with the HTTP request as content
For convenience the Request class has a **jsonData()** function that converts the binary data into a json object.

### The Response class
The **Response** class has by default a constructor with a HTTP status code. Various subclasses are available to add more functionality:
- **FileResponse**: Accepts a file name as parameter and will send the contents of the file as HTTP content body
- **ContentResponse**: Accepts a HTTP status code, bytes object for content data and a mime type as parameters
- **JsonResponse**: Accepts a json object as parameter which will be the HTTP content body
- **HtmlResponse**: Accepts HTML code (str object) as parameter (and optionally a HTTP status code)
For convenience there are several other Response subclasses, like **NotFound**, **NotModified**, **BadRequest**, **ServerError**, etc.
