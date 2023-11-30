from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import tdb.db
import tdb.cli
import tdb.html
import tdb.records
import contextlib
import threading
import json
import socket
import urllib.parse
import time
import os
import webbrowser

db_lock = threading.Lock()
running = True

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
        if query_list and self.path.startswith("/api/"):
            queries = {}
            for q in query_list:
                k, v = q.split("=", 1)
                queries[k] = v
            
            options = ("web "+urllib.parse.unquote(queries["opts"])) if "opts" in queries else ""
            options = tdb.cli.parse_options(options)
            # print("parsed options: "+str(options))

            response = {"ok": False}
            headers = {}
            headers["Content-Type"] = "text/json"

            if "/api/get.records" == self.path:
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
        elif any(map(self.path.endswith, [".js", ".html", ".css"])):
            headers = {}
            out = ""
            print(self.path)
            if "/tdb/html.js" == self.path:
                headers["Content-Type"] = "text/javascript"
                self.path = os.path.abspath(os.path.dirname(__file__)+"/html.js")
                out = open(self.path).read()
            elif "/tdb/mermaid.min.js" == self.path:
                headers["Content-Type"] = "text/javascript"
                self.path = tdb.html._mermaid_js_file
                out = open(self.path).read()
            elif "/tdb/mermaid.css" == self.path:
                headers["Content-Type"] = "text/css"
                self.path = tdb.html._mermaid_css_file
                out = open(self.path).read()
            elif "/tdb/style.css" == self.path:
                headers["Content-Type"] = "text/css"
                self.path = tdb.html._css_file
                out = open(self.path).read()
            elif "/index.html" == self.path:
                headers["Content-Type"] = "text/html"
                out = tdb.html.build_html([], True)
            self.send_response(200)
            for k, v in headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(bytes(out, "utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
        pass

    def do_POST(self):
        response = {"ok": False}
        if "/api/add.record" == self.path:
            try:
                db_lock.acquire()
                data_string = self.rfile.read(int(self.headers['Content-Length']))
                parsed = data_string.decode("utf-8")
                parsed = json.loads(parsed)
                if "record" in parsed:
                    tdb.records.add_record(parsed["record"])
                    response["ok"] = True
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
    global running
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
    print(f"Server started http://localhost:{addr[1]}")
    def update():
        global running
        while running:
            tdb.db.update()
            time.sleep(0.1)
    try:
        update_thread = threading.Thread(target=update)
        update_thread.start()
        webbrowser.open(f"http://localhost:{addr[1]}/index.html")
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    running = False
    update_thread.join(10)
    webServer.server_close()
    print("Server stopped.")

if __name__ == "__main__":
    start_server()
