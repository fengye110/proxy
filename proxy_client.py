import SocketServer
import  urllib2 ,base64
import logging


PROXY_USER_AGENT = 'proxy'

logging.basicConfig()
logger = logging.getLogger("ProxyclientHandler")

class ProxyClientHandler(SocketServer.BaseRequestHandler):
    def handle(self):

        client_data = self.get_client_data(self.request)
        logger.warning("client_data: len = %d\n%s", len(client_data), client_data)
        logger.warning("client_data:-- end\n")

        client_data = self.encodedata(client_data)

        logger.warning('encoding ok\n')
        respon = self.send2target(client_data)

        headers = respon.info()
        logger.warning('headers == \n')
        logger.warning(headers)

        logger.warning('sended \n')
        data = self.decodedata(respon.read())
        logger.warning('target data received\n \n')
        logger.warning("----target_data:----\n %s", data)
        respon.close()

        self.request.send(target_data)

    def init(self):
        try:
            self.target = urllib2.HTTPConnection(host, port, timeout= timeout)
        except httplib.HTTPException, e:
            logger.exception(e)

    def get_client_data(self, request):
        buflen = 1024
        return request.recv(buflen)

    def encodedata(self, data):
        return base64.encodestring(data)

    def decodedata(self, data):
        return base64.decodestring(data)

    def send2target(self, data):
        headers = {'User-Agent':PROXY_USER_AGENT, 'crypto':'base64'}
        url = "http://127.0.0.1:9998"

        req = urllib2.Request(url = url, data = data, headers = headers)
        return urllib2.urlopen(req)

    def get_target_data(self, respon):
        return data
        

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), ProxyClientHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
