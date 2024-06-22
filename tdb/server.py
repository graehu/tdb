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
opt_overrides = {}
running = True

class TdbServer(SimpleHTTPRequestHandler):
    """
    List files that are allowed to be sent
    """
    whitelist = []

    def do_GET(self):
        query_list = []
        allowedit = self.client_address[0] == "127.0.0.1"
        
        # split the query out if need be
        if "?" in self.path:
            self.path, query_list = self.path.split("?")
            if "&" in query_list:
                query_list = query_list.split("&")
            else:
                query_list = [query_list]
        
        # put the queries into a dict
        if self.path.startswith("/api/"):
            queries = {}
            for q in query_list:
                k, v = q.split("=", 1)
                queries[k] = v
            
            options = ("web "+urllib.parse.unquote(queries["opts"])) if "opts" in queries else ""
            options = tdb.cli.parse_options(options)

            for k in options:
                if isinstance(options[k], list) and k in opt_overrides: options[k] += opt_overrides[k]
                elif k in opt_overrides and opt_overrides[k]: options[k] = opt_overrides[k]

            response = {"ok": False}
            headers = {}
            headers["Content-Type"] = "text/json"

            if "/api/get.records" == self.path:
                response["ok"] = True
                response["records"] = tdb.records.stringify_db_records(options)
            elif "/api/get.tags" == self.path:
                print("getting tags - not implemented")
                response["ok"] = True
                response["tags"] = "not implemented"
            elif "/api/get.allowedit" == self.path:
                response["ok"] = True
                response["allowedit"] = allowedit
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
            if "/tdb/html.js" == self.path:
                headers["Content-Type"] = "text/javascript"
                self.path = os.path.abspath(os.path.dirname(__file__)+"/html.js")
                out = open(self.path, encoding="utf-8").read()
            elif "/tdb/mermaid.min.js" == self.path:
                headers["Content-Type"] = "text/javascript"
                self.path = tdb.html._mermaid_js_file
                out = open(self.path, encoding="utf-8").read()
            elif "/tdb/mermaid.css" == self.path:
                headers["Content-Type"] = "text/css"
                self.path = tdb.html._mermaid_css_file
                out = open(self.path, encoding="utf-8").read()
            elif "/tdb/style.css" == self.path:
                headers["Content-Type"] = "text/css"
                self.path = tdb.html._css_file
                out = open(self.path, encoding="utf-8").read()
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
        allowedit = self.client_address[0] == "127.0.0.1"
        code = 200
        headers = {}
        headers["Content-Type"] = "text/json"
        headers["Content-Length"] = 0
        try:
            db_lock.acquire()
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            parsed = data_string.decode("utf-8")
            parsed = json.loads(parsed)
            if "/api/add.record" == self.path and allowedit:
                if "text" in parsed:
                    tdb.records.add_record(parsed["text"])
                    response["ok"] = True
           
            elif "/api/edit.record" == self.path and allowedit:
                if "text" in parsed and "date" in parsed:
                    options = tdb.cli.parse_options("web")
                    options["dates"] = tdb.cli.parse_options("web "+parsed["date"])["dates"]
                    records = tdb.records.split_db_records(options)
                    if len(records) == 1:
                        cpy = tdb.records.Record(**records[0].asdict())
                        cpy.text = parsed["text"] 
                        cpy.text_hash = hash(cpy.text)
                        tdb.records.modify_db_records(records, [cpy])
                        tdb.db.serialise()
                        response["ok"] = True

            elif "/api/remove.record" == self.path and allowedit:
                if "date" in parsed:
                    options = tdb.cli.parse_options("web")
                    options["dates"] = tdb.cli.parse_options("web "+parsed["date"])["dates"]
                    records = tdb.records.split_db_records(options)
                    if len(records) == 1:
                        tdb.records.archive_records(records)
                        tdb.db.serialise()
                        response["ok"] = True

            else: code = 404
            payload = bytes(json.dumps(response)+"\r\n", "utf-8")
            headers["Content-Length"] = len(payload)
            self.send_response(code)
            for k, v in headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(payload)

        finally:
            db_lock.release()


def _get_best_family(*address):
    infos = socket.getaddrinfo(
        *address,
        type=socket.SOCK_STREAM,
        flags=socket.AI_PASSIVE,
    )
    family, type, proto, canonname, sockaddr = next(iter(infos))
    return family, sockaddr


def start_server(port=8000, options={}):
    global running
    global opt_overrides

    opt_overrides = options if options else {}
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
