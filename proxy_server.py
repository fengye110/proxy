from wsgiref.simple_server import make_server
from httplib import HTTPConnection
import logging
import base64
from rfc822 import Message

logging.basicConfig()
logger = logging.getLogger('ProxyServerHandler')

PROXY_USER_AGENT = 'proxy'

class proxy_server(object):
    def __call__(self, environ, start_response):
        return self.handler(environ, start_response)

    def handler(self, environ, start_response):
        self.env = environ
        self.start_response = start_response

        if environ.get('HTTP_USER_AGENT') == PROXY_USER_AGENT:
            return do_proxy()
        else:
            start_response("200 OK", [('Content-Type', 'text/html')])
            return ['hello world']

    def do_proxy(self):
        crypto = self.env['crypto']
        headers = {}

        if not self.env.get('CONTENT_LENGTH'):
            start_response("501 Gateway error", [('Content-Type', 'text/html')])
            return ['error content length']

        length = int(environ['CONTENT_LENGTH'])
        body = environ['wsgi.input'].read(length)
        logger.warning('body=\n%s', body)
        
        # decode data
        if crypto == 'base64':
            request_data = base64.decodestring(body)
        
        # get remote url
        end = request_data.find('\n')
        if end < 0:
            logger.exception("format error")
            start_response("501 Gateway error", [('Content-Type', 'text/html')])
            return []

        method, path, protocol = request_data[:end+1].split()
        rfile = StringIO()
        rfile.write(request_data(end+1:))
        headers = Message(rfile)
        # Make the remote request
        try:
            connection.request(method, path, body=body, headers=headers)
        except:
            # We need extra exception handling in the case the server fails in mid connection, it's an edge case but I've seen it
            start_response("501 Gateway error", [('Content-Type', 'text/html')])
            logger.exception('Could not Connect')
            return ['<H1>Could not connect</H1>']


    def send2client(self, req, data):
        req.send(data)

    def init(self):
        try:
            self.target = urllib2.HTTPConnection(host, port, timeout= timeout)
        except httplib.HTTPException, e:
            logger.exception(e)

    def get_client_data(self, request):
        buflen = 8092
        data = ''
        while True:
            logger.warning('-- recv -- \n')
            ret = request.recv(buflen)
            print ' === data len=%d== \n %s'%(len(ret),ret)
            if len(ret) < buflen:
                break
            data += ret
        return self.decodedata(data)

    def encodedata(self, data):
        return base64.encodestring(data)

    def decodedata(self, data):
        return base64.decodestring(data)

    def send2target(self, data):
        headers = {'User-Agent':'proxy', 'crypto':'base64'}
        url = "localhost:9998"

        req = urllib2.Request(url = url, data = data, headers = headers)
        return urllib2.urlopen(req)

    def get_target_data(self, respon):
        data = respon.read()
        return data
        
#def application(environ, start_response):
    #return proxy_server(environ, start_response)

if __name__ == "__main__":
    host, port = "127.0.0.1", 9998

    httpd = make_server(host, port, proxy_server)
    httpd.serve_forever()
