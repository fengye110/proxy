import SocketServer
import  urllib2 ,base64
import  httplib
import logging
from rfc822 import Message
from cStringIO import StringIO
import os
import zlib

ProxyServerAddr = 'localhost:9988'

logging.basicConfig()
logger = logging.getLogger("ProxyclientHandler")
#logger.setLevel(logging.DEBUG)


PROXY_USER_AGENT = 'proxy'
class ProxyClientHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        client_data = self.get_client_data(self.request)
        logger.debug("client_data: len = %d , --- client_data--\n%s\n==end==", len(client_data), client_data)

        # encode data
        client_data = self.encodedata('base64', client_data)

        conn,respon = self.send2target(client_data)

        # get respon headers
        headers = dict(respon.getheaders())

        # get data
        data = respon.read()
        conn.close()
        html = self.decodedata(headers.get('content-encoding'),data)

        self.send2client(html)

    def init(self):
        try:
            self.target = urllib2.HTTPConnection(host, port, timeout= timeout)
        except httplib.HTTPException, e:
            logger.exception(e)

    def get_client_data(self, request):
        buflen = 8072
        rfile = StringIO()
        # get header
        buf = request.recv(buflen)
        rfile.write(buf)

        rfile.seek(0)
        headers = Message(rfile,1)
        rfile.seek(0, os.SEEK_END)

        if headers.get('content_length'):
            clen = int(headers.get('content_length'))
            buf = request.recv(clen)
            rfile.write(buf)

        return  rfile.getvalue()

    def send2client(self, html):
        logger.debug('=== html ==\n%s\n== end ==\n', html[:600])
        self.request.sendall(html)

    def encodedata(self, method, data):
        self.encode_method = method
        if method == 'gzip':
            return zlib.compress(data)
        if method == 'base64':
            return base64.encodestring(data)

    def decodedata(self, method, data):
        if method == 'base64':
            return base64.decodestring(data)
        if method == 'gzip':
            return zlib.decompress(data)
        return data

    def send2target(self, data):
        headers = {'User-Agent':PROXY_USER_AGENT, 
                   'Content-Encode':self.encode_method}

        conn = httplib.HTTPConnection(ProxyServerAddr)
        conn.request("POST", "/", data, headers)

        return (conn, conn.getresponse())
        

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), ProxyClientHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
