#!/usr/bin/python
from __future__ import division, print_function
import numpy as np
import json
import traceback

from .microscope import STAGE_AXES

# Get imports from library
# Python 3.X
import asyncio
from aiohttp import web, WSMsgType


# Numpy array encoding JSON encoder
class ArrayJSONEncoder(json.JSONEncoder):
    allowed_dtypes = {"INT8", "INT16", "INT32", "INT64", "UINT8", "UINT16", "UINT32", "UINT64", "FLOAT32", "FLOAT64"}

    def default(self, obj):
        if isinstance(obj, np.ndarray):
            import sys, base64

            dtype_name = obj.dtype.name.upper()
            if dtype_name not in self.allowed_dtypes:
                return json.JSONEncoder.default(self, obj)

            if obj.dtype.byteorder == '<':
                endian = "LITTLE"
            elif obj.dtype.byteorder == '>':
                endian = "BIG"
            else:
                endian = sys.byteorder.upper()

            return {
                'width': obj.shape[1],
                'height': obj.shape[0],
                'type': dtype_name,
                'endianness': endian,
                'encoding': "BASE64",
                'data': base64.b64encode(obj).decode("ascii")
            }
        return json.JSONEncoder.default(self, obj)


def _gzipencode(content):
    """GZIP encode bytes object"""
    import gzip
    out = BytesIO()
    f = gzip.GzipFile(fileobj=out, mode='w', compresslevel=5)
    f.write(content)
    f.close()
    return out.getvalue()


def _parse_enum(type, item):
    """Try to parse 'item' (string or integer) to enum 'type'"""
    try:
        return type[item]
    except:
        return type(item)

class MicroscopeServerWithEvents:
    """
    Implements the same HTTP server as server.py
    Additionally polls the current state of the Titan microscope
    and -in case of any changes- sends an event via a websocket
    connection.

    HTTP-URLs are supposed to follow the format
        http://127.0.0.1:8080/v1/...
    Websocket connections are initialized via the websocket URL
        ws://127.0.0.1:8080/ws/
    """

    def __init__(self):
        # set of client references
        self.clients = set()
        self.clients_lock = asyncio.Lock()

    async def http_handler(self, request):
        ws = web.WebSocketResponse()
        for ws in self.clients:
            await ws.send_str("WEBSOCKETEVENT from {}".format(request.match_info['name']))
        return web.Response(text="HTTP for {}".format(request.match_info['name']))

    async def websocket_handler(self, request):
        print("Websocket handler called")
        ws = web.WebSocketResponse()
        # add client to set
        await self.add_websocket_client(ws)
        await ws.prepare(request)

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
                else:
                    await ws.send_str(msg.data + '/answer')
            elif msg.type == WSMsgType.ERROR:
                await self.remove_websocket_client(ws)
                print('ws connection closed with exception %s' %
                      ws.exception())
            else:
                print('Unsupported websocket message type %s' % msg.type)

        await self.remove_websocket_client(ws)
        print('websocket connection closed')

        return ws

    async def add_websocket_client(self, ws):
        async with self.clients_lock:
            print("number of clients before adding new client: %s " % len(self.clients))
            self.clients.add(ws)
            print("number of clients after adding new client: %s " % len(self.clients))

    async def remove_websocket_client(self, ws):
        async with self.clients_lock:
            print("number of clients before removing client: %s " % len(self.clients))
            self.clients.remove(ws)
            print("number of clients after removing client: %s " % len(self.clients))

    def run_server(self):
        app = web.Application()
        # app.add_routes([web.get('/ws', websocket_handler), web.get('/v1', hello)]) # ws://127.0.0.1:8080/ws
        app.add_routes([web.get('/ws', self.websocket_handler),  # ws://127.0.0.1:8080/ws/
                        web.get(r'/v1/{name:.+}', self.http_handler)])  # http://127.0.0.1:8080/v1/*

        web.run_app(app)  # port=8888

if __name__ == '__main__':
    server = MicroscopeServerWithEvents()
    server.run_server()
