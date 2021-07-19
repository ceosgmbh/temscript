#!/usr/bin/python
from __future__ import division, print_function
import numpy as np
import json

# Get imports from library
# Python 3.X
import asyncio
from aiohttp import web, WSMsgType

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
    :param host IP the webserver is running under. Default is "0.0.0.0"
                (run on all interfaces)
    :type host str
    :param port Port the webserver is running under. Default is "8080"
                (default HTTP-port)
    :type port int
    :param microscope the Microscope to use (either NullMicroscope()
                or Microscope())
    :type microscope Microscope
    """

    def __init__(self, microscope, host="0.0.0.0", port=8080):
        self.host = host
        self.port = port
        self.microscope = microscope
        print("Configuring web server for host=%s, port=%s" % (self.host, self.port))
        # set of client references
        self.clients = set()
        self.clients_lock = asyncio.Lock()

    async def http_get_handler_v1(self, request):
        # ws = web.WebSocketResponse()
        # for ws in self.clients:
        #     await ws.send_str("WEBSOCKETEVENT-GET from {}".format(request.match_info['name']))
        # get query string (only used for http://<host>:>port/v1/acquire?detectors=<detectors>)
        command = request.match_info['name']
        parameter = request.rel_url.query
        response=''
        try:
            response = self.do_GET_V1(command, parameter)
            if response is None:
                # unsupported command: send status 204
                return web.Response(body="Unsupported command {}"
                                    .format(command),
                                    status=204)
            else:
                # send JSON response and (default) status 200
                encoded_response = ArrayJSONEncoder()\
                    .encode(response).encode("utf-8")
                return web.Response(body=encoded_response,
                                    content_type="application/json")
        except MicroscopeException as e:
            # regular exception due to misconfigurations etc.: send error status 404
            return web.Response(body=e, status=404)
        except Exception as e:
            # any exception beyond that: send error status 500
            return web.Response(body=e, status=500)

    # Handler for V1 GETs
    def do_GET_V1(self, command, parameter):
        # Check for known endpoints
        response = None
        if command == "family":
            response = self.microscope.get_family()
        elif command == "microscope_id":
            response = self.microscope.get_microscope_id()
        elif command == "version":
            response = self.microscope.get_version()
        elif command == "voltage":
            response = self.microscope.get_voltage()
        elif command == "vacuum":
            response = self.microscope.get_vacuum()
        elif command == "stage_holder":
            response = self.microscope.get_stage_holder()
        elif command == "stage_status":
            response = self.microscope.get_stage_status()
        elif command == "stage_position":
            response = self.microscope.get_stage_position()
        elif command == "stage_limits":
            response = self.microscope.get_stage_limits()
        elif command == "detectors":
            response = self.microscope.get_detectors()
        elif command == "image_shift":
            response = self.microscope.get_image_shift()
        elif command == "beam_shift":
            response = self.microscope.get_beam_shift()
        elif command == "beam_tilt":
            response = self.microscope.get_beam_tilt()
        elif command == "instrument_mode":
            response = self.microscope.get_instrument_mode()
        elif command == "instrument_mode_string":
            response = self.microscope.get_instrument_mode_string()
        elif command == "df_mode":
            response = self.microscope.get_df_mode()
        elif command == "df_mode_string":
            response = self.microscope.get_df_mode_string()
        elif command == "projection_sub_mode":
            response = self.microscope.get_projection_sub_mode()
        elif command == "projection_mode":
            response = self.microscope.get_projection_mode()
        elif command == "projection_mode_string":
            response = self.microscope.get_projection_mode_string()
        elif command == "projection_mode_type_string":
            response = self.microscope.get_projection_mode_type_string()
        elif command == "illumination_mode":
            response = self.microscope.get_illumination_mode()
        elif command == "illumination_mode_string":
            response = self.microscope.get_illumination_mode_string()
        elif command == "illuminated_area":
            response = self.microscope.get_illuminated_area()
        elif command == "condenser_mode":
            response = self.microscope.get_condenser_mode()
        elif command == "condenser_mode_string":
            response = self.microscope.get_condenser_mode_string()
        elif command == "spot_size_index":
            response = self.microscope.get_spot_size_index()
        elif command == "magnification_index":
            response = self.microscope.get_magnification_index()
        elif command == "stem_magnification":
            response = self.microscope.get_stem_magnification()
        elif command == "indicated_camera_length":
            response = self.microscope.get_indicated_camera_length()
        elif command == "indicated_magnification":
            response = self.microscope.get_indicated_magnification()
        elif command == "defocus":
            response = self.microscope.get_defocus()
        elif command == "probe_defocus":
            response = self.microscope.get_probe_defocus()
        elif command == "objective_excitation":
            response = self.microscope.get_objective_excitation()
        elif command == "intensity":
            response = self.microscope.get_intensity()
        elif command == "objective_stigmator":
            response = self.microscope.get_objective_stigmator()
        elif command == "condenser_stigmator":
            response = self.microscope.get_condenser_stigmator()
        elif command == "diffraction_shift":
            response = self.microscope.get_diffraction_shift()
        elif command == "optics_state":
            response = self.microscope.get_optics_state()
        elif command == "beam_blanked":
            response = self.microscope.get_beam_blanked()
        elif command.startswith("detector_param/"):
            try:
                name = command[15:]
                response = self.microscope.get_detector_param(name)
            except KeyError:
                raise MicroscopeException('Unknown detector: %s' % self.path)
                #self.send_error(404, 'Unknown detector: %s' % self.path)
                #return
        elif command == "acquire":
            try:
                detectors = parameter["detectors"]
            except KeyError:
                # self.send_error(404, 'No detectors: %s' % self.path)
                # return
                raise MicroscopeException('No detectors: %s' % self.path)
            response = self.microscope.acquire(*detectors)
        else:
            # self.send_error(404, 'Unknown endpoint: %s' % self.path)
            # return
            raise MicroscopeException('Unknown endpoint: %s' % self.path)
        return response

    async def http_put_handler_v1(self, request):
        # ws = web.WebSocketResponse()
        # for ws in self.clients:
        #     await ws.send_str("WEBSOCKETEVENT-PUT from {}".format(request.match_info['name']))
        return web.Response(text="HTTP-PUT for {}".format(request.match_info['name']))

    # # Handler for V1 PUTs
    # def do_PUT_V1(self, endpoint, query):
    #     # Read content
    #     length = int(self.headers['Content-Length'])
    #     if length > 4096:
    #         raise ValueError("Too much content...")
    #     content = self.rfile.read(length)
    #     decoded_content = json.loads(content.decode("utf-8"))
    #
    #     # Check for known endpoints
    #     response = None
    #     if endpoint == "stage_position":
    #         method = decoded_content.get("method", "GO")
    #         pos = dict((k, decoded_content[k]) for k in decoded_content.keys() if k in STAGE_AXES)
    #         try:
    #             pos['speed'] = decoded_content['speed']
    #         except KeyError:
    #             pass
    #         self.microscope.set_stage_position(pos, method=method)
    #     elif endpoint == "image_shift":
    #         self.microscope.set_image_shift(decoded_content)
    #     elif endpoint == "beam_shift":
    #         self.microscope.set_beam_shift(decoded_content)
    #     elif endpoint == "beam_tilt":
    #         self.microscope.set_beam_tilt(decoded_content)
    #     elif endpoint == "df_mode":
    #         self.microscope.set_df_mode(decoded_content)
    #     elif endpoint == "illuminated_area":
    #         self.microscope.set_illuminated_area(decoded_content)
    #     elif endpoint == "projection_mode":
    #         self.microscope.set_projection_mode(decoded_content)
    #     elif endpoint == "magnification_index":
    #         self.microscope.set_magnification_index(decoded_content)
    #     elif endpoint == "stem_magnification":
    #         self.microscope.set_stem_magnification(decoded_content)
    #     elif endpoint == "defocus":
    #         self.microscope.set_defocus(decoded_content)
    #     elif endpoint == "probe_defocus":
    #         self.microscope.set_probe_defocus(decoded_content)
    #     elif endpoint == "intensity":
    #         self.microscope.set_intensity(decoded_content)
    #     elif endpoint == "diffraction_shift":
    #         self.microscope.set_diffraction_shift(decoded_content)
    #     elif endpoint == "objective_stigmator":
    #         self.microscope.set_objective_stigmator(decoded_content)
    #     elif endpoint == "condenser_stigmator":
    #         self.microscope.set_condenser_stigmator(decoded_content)
    #     elif endpoint == "beam_blanked":
    #         self.microscope.set_beam_blanked(decoded_content)
    #     elif endpoint.startswith("detector_param/"):
    #         try:
    #             name = endpoint[15:]
    #             response = self.microscope.set_detector_param(name, decoded_content)
    #         except KeyError:
    #             self.send_error(404, 'Unknown detector: %s' % self.path)
    #             return
    #     elif endpoint == "normalize":
    #         mode = decoded_content
    #         try:
    #             self.microscope.normalize(mode)
    #         except ValueError:
    #             self.send_error(404, 'Unknown mode.' % mode)
    #             return
    #     else:
    #         self.send_error(404, 'Unknown endpoint: %s' % self.path)
    #         return
    #     self.build_response(response)


    async def websocket_handler_v1(self, request):
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
        print("Starting web server with events under host=%s, port=%s" % (self.host, self.port))
        app = web.Application()
        # add routes for
        # - HTTP-GET/PUT, e.g. http://127.0.0.1:8080/v1/projection_mode
        # - websocket connection ws://127.0.0.1:8080/ws/v1
        app.add_routes([web.get('/ws/v1', self.websocket_handler_v1),  #
                        web.get(r'/v1/{name:.+}', self.http_get_handler_v1),
                        web.put(r'/v1/{name:.+}', self.http_put_handler_v1),
                        ])

        web.run_app(app, host=self.host, port=self.port)

class MicroscopeException(Exception):
    def __init__(self, *args, **kw):
        super(MicroscopeException, self).__init__(*args, **kw)

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


if __name__ == '__main__':
    host="0.0.0.0"
    port=8080
    from .microscope import Microscope
    microscope = Microscope()
    server = MicroscopeServerWithEvents(microscope=microscope,
                                        host=host, port=port)
    server.run_server()
