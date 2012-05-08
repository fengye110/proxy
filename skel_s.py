import SocketServer
import  urllib2 ,base64
import logging


PROXY_USER_AGENT = 'proxy'

logging.basicConfig()
logger = logging.getLogger("ProxyclientHandler")


class ProxyClientHandler(SocketServer.BaseRequestHandler):
    def handle(self):

        client_data = self.get_client_data(self.request)
if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), ProxyClientHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
