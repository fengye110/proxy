from wsgiref.simple_server import make_server
from httplib import HTTPConnection
import httplib
import logging
import base64
from rfc822 import Message
from cStringIO import StringIO
from urlparse import urlparse
import zlib

logging.basicConfig()
logger = logging.getLogger('Svr')
#logger.setLevel(logging.DEBUG)

PROXY_USER_AGENT = 'proxy'
CRLF = "\r\n"

_hoppish = {
    'connection':1, 'keep-alive':1, 'proxy-authenticate':1,
    'proxy-authorization':1, 'te':1, 'trailers':1, 'transfer-encoding':1,
    'upgrade':1, 'proxy-connection':1 }
    
def is_hop_by_hop(header):
    return _hoppish.has_key(header.lower())

class proxy_server(object):
    def __call__(self, environ, start_response):
        return self.handler(environ, start_response)

    def handler(self, environ, start_response):
        self.env = environ
        self.start_response = start_response
        self.crypto_en_method =''

        if environ.get('HTTP_USER_AGENT') == PROXY_USER_AGENT:
            return self.do_proxy()
        else:
            start_response("200 OK", [('Content-Type', 'text/html')])
            return ['hello world']

    def do_proxy(self):
        if not self.env.get('CONTENT_LENGTH'):
            self.start_response("411 Length Required", [('Content-Type', 'text/html')])
            return ['Length Required']

        # get and decode data
        _body = self.env['wsgi.input'].read(int(self.env.get('CONTENT_LENGTH')))
        request_data = self.decodedata(self.env.get('HTTP_CONTENT_ENCODE',''), _body)
        
        # get remote url
        end = request_data.find('\n')
        if end < 0:
            logger.exception("format error")
            self.start_response("501 Gateway error", [('Content-Type', 'text/html')])
            return ['format error']

        logger.debug("\n== req_data ==\n%s\n== end ==\n", request_data)
        method, path, protocol = request_data[:end+1].split()
        url = urlparse(path)
        path = url.geturl().replace('%s://%s' % (url.scheme, url.netloc), '')
        logger.debug("\n== url ==\n%s\n== end ==\n", url)

        # get headers
        rfile = StringIO()
        rfile.write(request_data[end+1:])
        rfile.seek(0)
        headers = dict(Message(rfile,1))

        # get body
        body=None
        if headers.get('content_length'):
            ret = request_data.find('\r\n\r\n')
            body = request_data[ret + 4:]
        #logger.debug('body=---\n%s', body)
        # Make the remote request
        try:
            con = httplib.HTTPConnection(url.netloc, timeout=30)
            logger.debug('%s %s %s' % ( method, path, str(headers)))
            logger.debug('body: %s' %(body))
            con.request(method, path, body=body, headers=headers)
            rep = con.getresponse()
            data = rep.read()
            rmt_headers = rep.getheaders()
            con.close()
        except:
            # We need extra exception handling in the case the server fails in mid connection, it's an edge case but I've seen it
            logger.exception('Could not Connect')
            self.start_response("501 Gateway error", [('Content-Type', 'text/html')])
            return ['<H1>Could not connect</H1>']

        # remove dummy headers
        for header in rmt_headers:
            if is_hop_by_hop(header[0]):
                rmt_headers.remove(header)
        rmt_headers = dict(rmt_headers)

        headers_str = ''
        for key, value in rmt_headers.items():
            headers_str = headers_str + "%s: %s\r\n"%(key, value)

        #  build and encode  data
        ret_data = "HTTP/%0.1f %s %s\r\n"%(rep.version/10.0, rep.status, rep.reason) + headers_str + "\r\n" + data 
        ret_data = zlib.compress(ret_data)

        headers=[('Content-Type', 'text/html'),
                 ('Content-Encoding', 'gzip'),
                 ('Content-Length',str(len(ret_data)))]

        #logger.debug('== ret_data =\n%s\n==end==', ret_data)
        self.start_response("200 OK", headers)
        return [ret_data]


    def encodedata(self, data):
        self.crypto_en_method = self.crypto_de_method
        if self.crypto_en_method == 'base64':
            return base64.encodestring(data)
        return data

    def decodedata(self, method, data):
        if method == 'base64':
            return base64.decodestring(data)
        if method == 'gzip':
            return zlib.decompress(data)
        return data

        
def application(environ, start_response):
    a = proxy_server()
    return a(environ, start_response)

if __name__ == "__main__":
    host, port = "localhost", 9988

    httpd = make_server(host, port, application)
    httpd.serve_forever()
