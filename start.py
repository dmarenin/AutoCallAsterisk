from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from common import ami_client
import sys
from common import common

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
    parser = common.createParser()
    namespace = parser.parse_args(sys.argv[1:])
    api_ones_serv = ami_client.AmiClient()
    server = ThreadedHTTPServer((namespace.ip, int(namespace.port)), ami_client.AmiClient_Handler)
    print('starting ami client server '+str(namespace.ip)+':'+str(namespace.port)+' (use <Ctrl-C> to stop)')
    server.serve_forever()


