from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import tdb.cli
import tdb.records
import contextlib
import threading
import json
import socket
import urllib.parse


db_lock = threading.Lock()

class TdbServer(SimpleHTTPRequestHandler):
    """
    List files that are allowed to be sent
    """
    whitelist = []

    def do_GET(self):
        query_list = None

        # split the query out if need be
        if "?" in self.path:
            self.path, query_list = self.path.split("?")
            if "&" in query_list:
                query_list = query_list.split("&")
            else:
                query_list = [query_list]
        
        # put the queries into a dict        
        if query_list:
            queries = {}
            for q in query_list:
                k, v = q.split("=")
                queries[k] = v
            
            options = ("web "+urllib.parse.unquote(queries["opts"])) if "opts" in queries else ""
            options = tdb.cli.parse_options(options)
            print("parsed options: "+str(options))
            response = {"ok": False}
            headers = {}
            headers["Content-Type"] = "text/json"

            if "/api/get.records" == self.path:
                print("getting records")
                response["ok"] = True
                response["records"] = tdb.records.stringify_records(options)
            elif "/api/get.tags" == self.path:
                print("getting tags")
                response["ok"] = True
                response["tags"] = "not implemented"
            else:
                self.send_response(404)
                for k, v in headers.items():
                    self.send_header(k, v)
                response["error"] = "api call not found "+self.path
                self.end_headers()
                self.wfile.write(bytes(json.dumps(response), "utf-8"))
                return

            self.send_response(200)
            for k, v in headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(bytes(json.dumps(response), "utf-8"))
            return
        else:
            self.send_response(404)
            self.end_headers()
        pass

    def do_POST(self):
        response = {"ok": False}
        if "/api/add.records" == self.path:
            try:
                db_lock.acquire()
                response["ok"] = True
                data_string = self.rfile.read(int(self.headers['Content-Length']))
                parsed = data_string.decode("utf-8")
                parsed = json.loads(parsed)
                print(parsed)
            finally:
                db_lock.release()
                pass
            self.send_response(200)
            self.end_headers()
            self.wfile.write(bytes(json.dumps(response), "utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes(json.dumps(response), "utf-8"))


def _get_best_family(*address):
    infos = socket.getaddrinfo(
        *address,
        type=socket.SOCK_STREAM,
        flags=socket.AI_PASSIVE,
    )
    family, type, proto, canonname, sockaddr = next(iter(infos))
    return family, sockaddr


def start_server(port=8000):
    # ensure dual-stack is not disabled; ref #38907
    class DualStackServer(ThreadingHTTPServer):
        def server_bind(self):
            # suppress exception when protocol is IPv4
            with contextlib.suppress(Exception):
                self.socket.setsockopt(
                    socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            return super().server_bind()

    # this is required to work with safari for some reason.
    DualStackServer.address_family, addr = _get_best_family(None, port)

    webServer = DualStackServer(addr, TdbServer)
    print("Server started http://%s:%s" % (addr))
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")

if __name__ == "__main__":
    start_server()