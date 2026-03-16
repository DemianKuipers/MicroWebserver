"""
MicroWebserver is a lightweight HTTP server for MicroPython

MIT License

Copyright (c) 2026 Demian Kuipers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import socket
import io
import json
from os import stat
from time import sleep

class ServerException(Exception):
    pass

class RequestException(ServerException):
    pass

class Request:
    
    def __init__(self, client, timeout=30):

        rawdata = client.recv(1024)

        # Determine header data
        headerEndIndex = rawdata.index(b'\r\n\r\n')
        headerString = rawdata[0:headerEndIndex].decode('utf-8')
        rawHeaders = headerString.split('\r\n')
    
        requestLine = rawHeaders[0].split()
        if len(requestLine) < 2:
            raise RequestException('Malformed request line')
        self.method = requestLine[0]
        self.uri = requestLine[1]
        del rawHeaders[0]
        print(f'HTTP Server request: {self.method} {self.uri}')
        
        # Request parameters
        self.params = {}
        q = self.uri.find('?')
        if q < 0:
            self.path = self.uri
        else:
            self.path = self.uri[0:q]
            pars = self.uri[q+1:]
            prs = pars.split('&')
            for pr in prs:
                pm = pr.split('=', 1)
                if len(pm) != 2:
                    raise RequestException('Malformed parameter')
                self.params[pm[0]] = pm[1]
    
        self.headers = {}
        for rawHeader in rawHeaders:
            rh = rawHeader.split(': ', 1)
            if len(rh) != 2:
                raise RequestException('Malformed header')
            self.headers[rh[0]] = rh[1]

        # Get data (commonly sent with POST/PUT)
        data = bytearray()
        startpos = headerEndIndex + 4
        if startpos < len(rawdata):
            data = bytearray(rawdata[startpos:])
        
        if 'Content-Length' in self.headers:
            contentLength = int(self.headers['Content-Length'])
            if len(data) < contentLength:
                count = 0
                while count < 100 and len(data) < contentLength:
                    sleep(timeout / 100)
                    count += 1
                    rawdata = client.recv(1024)
                    if len(rawdata) > 0:
                        data.extend(rawdata)
                if len(data) < contentLength:
                    raise RequestException('Incomplete request data')

        self.data = data

    def jsonData(self):
        if len(self.data) > 0:
            if 'Content-Type' in self.headers:
                ct = self.headers['Content-Type']
                if ct == 'application/json':
                    s = str(self.data, 'utf-8')
                    return json.loads(s)
        return None


class Status:
    
    reasons = { 200: 'OK',
                201: 'Created',
                202: 'Accepted',
                204: 'No Content',
                301: 'Moved Permanently',
                302: 'Found',
                304: 'Not Modified',
                400: 'Bad Request',
                401: 'Unauthorized',
                403: 'Forbidden',
                404: 'Not Found',
                500: 'Internal Server Error',
                501: 'Not Implemented',
                502: 'Bad Gateway',
                503: 'Service Unavailable' }
    
    def __init__(self, code):
        self.code = code

    def __str__(self):
        reason = self.reasons[self.code]
        return f'HTTP/1.1 {self.code} {reason}\n'


class MimeType:
    
    extensions = { 'txt': 'text/plain',
                   'html': 'text/html',
                   'xml': 'text/xml',
                   'css': 'text/css',
                   'json': 'application/json',
                   'png': 'image/png',
                   'jpg': 'image/jpeg',
                   'svg': 'image/svg+xml' }
    
    def find(filename):
        ep = filename.find('.')
        if ep < 0:
            return None
        ext = filename[ep+1:]
        if ext in MimeType.extensions:
            return MimeType.extensions[ext]
        return None


class Response:
    
    def __init__(self, code):
        self.code = code
        self.headers = {}
        self.data = None
        
    def __str__(self):
        send = str(Status(self.code))
        for key, value in self.headers.items():
            send += key + ': ' + value + '\r\n'
        send += '\r\n'
        return send
    
    def send(self, client):
        headers = bytearray(self.__str__(), 'utf-8')
        client.send(headers)
        if self.data is not None:
            client.send(self.data)


class FileResponse(Response):
    def __init__(self, filename, mime_type = None, code = 200):
        super().__init__(code)
        size = stat(filename)[6]	# ST_SIZE = 6
        self.headers['Content-Length'] = str(size)
        if mime_type is None:
            mime_type = MimeType.find(filename)
            if mime_type is None:
                mime_type = 'application/octet-stream'	# Default
        self.headers['Content-Type'] = mime_type
        self.data = None
        self._filename = filename

    def send(self, client):
        super().send(client)
        buffer = bytearray(1024)
        with open(self._filename, "rb") as file:
            while True:
                n = file.readinto(buffer)
                if n == 0:
                    break
                client.write(buffer[:n])


class ContentResponse(Response):
    
    def __init__(self, code, data, mime_type):
        super().__init__(code)
        self.headers['Content-Length'] = str(len(data))
        self.headers['Content-Type'] = mime_type
        self.data = data


class JsonResponse(ContentResponse):

    def __init__(self, jsonData):
        super().__init__(200, json.dumps(jsonData), 'application/json')


class Ok(ContentResponse):

    def __init__(self, data, mime_type):
        super().__init__(200, data, mime_type)


class NoContent(Response):
    
    def __init__(self, code):
        super().__init__(204)


class HtmlResponse(ContentResponse):
    
    def __init__(self, html, code = 200):
        super().__init__(code, bytes(html, 'utf-8'), 'text/html')
    

class DefaultResponse(HtmlResponse):
    
    def __init__(self, code, text = None):
        msg = ''
        if text is not None:
            msg = f': {text}'
        super().__init__(bytes(f'{code} {Status.reasons[code]}{msg}', 'utf-8'), code)


class NotFound(DefaultResponse):
    
    def __init__(self):
        super().__init__(404)


class NotModified(DefaultResponse):
    
    def __init__(self):
        super().__init__(304)


class BadRequest(DefaultResponse):
    def __init__(self, text = None):
        super().__init__(400, text)
        

class ServerError(DefaultResponse):
    
    def __init__(self, text = None):
        super().__init__(500, text)


class Server:
    
    def __init__(self, host="0.0.0.0", port=80, timeout=30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._routes = dict()
        self._server = None

    def route(self, method="GET", path="/"):
        if (method, path) in self._routes:
            raise ServerException(f'route {(method, path)} was already registered')
        def wrapper(function):
            self._routes[(method, path)] = function
        return wrapper
    
    def isConnected(self):
        return self._server is not None

    def start(self):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((self.host, self.port))
        self._server.listen(1)
        self._server.settimeout(0.1)
        try:
            self._hasWebFolder = stat('/www')[0] == 0x4000	# S_ISDIR
        except OSError as ose:
            if ose.errno == 2:
                self._hasWebFolder = False
            else:
                raise
    
    def stop(self):
        self._server.close()
        self._server = None
    
    def checkRequest(self):
        try:
            client = self._server.accept()[0]
            try:
                request = Request(client, self.timeout)
                
                function = self._routes.get((request.method, request.path))
                if function:
                    response = function(request)
                else:
                    if request.method == 'GET' and self._hasWebFolder:
                        if request.path.find('..') >= 0:
                            raise RequestException('Invalid path')
                        else:
                            file = '/www' + request.path
                            try:
                                isFile = stat(file)[0] == 0x8000	#S_ISREG
                            except OSError as ose:
                                if ose.errno == 2:	#ENOENT
                                    isFile = False
                                else:
                                    raise
                            if isFile:
                                response = FileResponse(file)
                            else:
                                response = NotFound()
                    else:
                        response = NotFound()
                response.send(client)
            except RequestException as re:
                response = BadRequest(str(re))
                response.send(client)
            except Exception as e:
                ec = type(e).__name__
                print(f'Server error: {ec} {e}')
                response = ServerError(str(ec) + ' ' + str(e))
                response.send(client)
            finally:
                client.close()
        except OSError as e:
            if e.errno == 110:
                return None
            else:
                raise
