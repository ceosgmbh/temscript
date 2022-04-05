#!/usr/bin/python
from __future__ import division, print_function

# require python 3.8 for aiohttp
import sys
if sys.hexversion < 0x03080000:
    sys.exit("Python 3.8 (32 bit) or newer is required to run this program.")

import os
import argparse

import numpy as np
import json
from io import BytesIO
import asyncio
from aiohttp import web, WSMsgType
# import traceback

# from functools import partial
from temscript import server_config
from temscript import logger

# initialize logger
log = logger.getLoggerForModule("TemscriptingServer")

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
        log.info("Configuring web server for host=%s, port=%s" % (self.host, self.port))

        # a dict for storing polling results
        self.microscope_state = dict()
        self.microscope_state_lock = asyncio.Lock()
        # set of client references
        self.clients = set()
        self.clients_lock = asyncio.Lock()


    async def http_get_handler_v1(self, request):
        """
        aiohttp handler fur GET request for V1
        :param request: the aiohttp GET request
        :return:  the aiohttp response
        """
        command = request.match_info['name']
        parameter = request.rel_url.query
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

    def do_GET_V1(self, command, parameter):
        """
        Handler for HTTP V1 GET requests
        :param command: The GET command to execute
        :param parameter: optional query parameter ,
                          see "acquire" command
        """
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
        elif command == "voltage_offset":
            # HT offset supported by StdScript 7.10
            response = self.microscope.get_voltage_offset()
        elif command.startswith("detector_param/"):
            try:
                name = command[15:]
                response = self.microscope.get_detector_param(name)
            except KeyError:
                raise MicroscopeException('Unknown detector: %s' % command)
        elif command == "acquire":
            try:
                detectors = parameter["detectors"]
            except KeyError:
                raise MicroscopeException('No detectors: %s' % command)
            response = self.microscope.acquire(*detectors)
        else:
            raise MicroscopeException('Unknown endpoint: %s' % command)
        # log.debug('Returning response %s for command %s...' % (response, command))
        return response

    async def http_put_handler_v1(self, request):
        """
        aiohttp handler fur PUT request for V1
        :param request: the aiohttp PUT request
        :return:  the aiohttp response
        """
        command = request.match_info['name']
        content_length = request.headers['content-length']
        if content_length is not None:
            if int(content_length) > 4096:
                raise ValueError("Too much content...")
        try:
            # get JSON content
            text_content = await request.text()
            json_content = json.loads(text_content)
            response = self.do_PUT_V1(command, json_content)
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

    def do_PUT_V1(self, command, json_content):
        """
        Handler for HTTP V1 PUT requests
        :param command: The PUT command to execute
        :param json_content: the content/value to set
        """
        response = None
        # Check for known endpoints
        if command == "stage_position":
            method = json_content.get("method", "GO")
            pos = dict((k, json_content[k]) for k in json_content.keys() if k in self.microscope.STAGE_AXES)
            try:
                pos['speed'] = json_content['speed']
            except KeyError:
                pass
            self.microscope.set_stage_position(pos, method=method)
        elif command == "image_shift":
            self.microscope.set_image_shift(json_content)
        elif command == "beam_shift":
            self.microscope.set_beam_shift(json_content)
        elif command == "beam_tilt":
            self.microscope.set_beam_tilt(json_content)
        elif command == "df_mode":
            self.microscope.set_df_mode(json_content)
        elif command == "illuminated_area":
            self.microscope.set_illuminated_area(json_content)
        elif command == "projection_mode":
            self.microscope.set_projection_mode(json_content)
        elif command == "magnification_index":
            self.microscope.set_magnification_index(json_content)
        elif command == "stem_magnification":
            self.microscope.set_stem_magnification(json_content)
        elif command == "defocus":
            self.microscope.set_defocus(json_content)
        elif command == "probe_defocus":
            self.microscope.set_probe_defocus(json_content)
        elif command == "intensity":
            self.microscope.set_intensity(json_content)
        elif command == "diffraction_shift":
            self.microscope.set_diffraction_shift(json_content)
        elif command == "objective_stigmator":
            self.microscope.set_objective_stigmator(json_content)
        elif command == "condenser_stigmator":
            self.microscope.set_condenser_stigmator(json_content)
        elif command == "beam_blanked":
            self.microscope.set_beam_blanked(json_content)
        elif command == "voltage_offset":
            # HT offset supported by StdScript 7.10
            self.microscope.set_voltage_offset(json_content)
        elif command.startswith("detector_param/"):
            try:
                name = command[15:]
                response = self.microscope.set_detector_param(name, json_content)
            except KeyError:
                raise MicroscopeException('Unknown detector: %s' % command)
        elif command == "normalize":
            mode = json_content
            try:
                self.microscope.normalize(mode)
            except ValueError:
                raise MicroscopeException('Unknown mode: %s' % mode)
        else:
            raise MicroscopeException('Unknown endpoint: %s' % command)
        return response

    async def websocket_handler_v1(self, request):
        """
        The aiohttp handler for websocket requests
        :param request: The connection request
        :return: the websocket response
        """
        log.debug('Websocket client session opened.')
        # available options for WebSocketResponse client session:
        #   autoping=True (default), heartbeat=5 (necessary for pings)
        #   receive_timeout=10
        ws = web.WebSocketResponse()
        remote_ip = request.remote
        log.info('Websocket handler for IP %s created.' % remote_ip)
        await ws.prepare(request)
        # add client to set
        await self.add_websocket_client(ws)

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    if msg.data != 'close':
                        log.warn('websocket connection received unsupported text message: "%s"' % msg.data)
                    await ws.close()
                elif msg.type == WSMsgType.PING:
                    pass
                    # log.debug('websocket connection received PING')
                elif msg.type == WSMsgType.PONG:
                    pass
                    # log.debug('websocket connection received PONG')
                elif msg.type == WSMsgType.ERROR:
                    await self.remove_websocket_client(ws)
                    log.exception('websocket connection closed with exception %s' %
                          ws.exception())
                    await ws.close()
                else:
                    log.warn('Received unsupported websocket message type "%s": closing connection' % msg.type)
                    await ws.close()
        finally:
            log.info('Websocket client session closed for IP %s' % remote_ip)
            await ws.close()
            await self.remove_websocket_client(ws)

        return ws

    async def add_websocket_client(self, ws):
        async with self.clients_lock:
            # log.debug('number of clients before adding new client: %s ' %
            #       len(self.clients))
            self.clients.add(ws)
            log.debug('number of clients after adding new client: %s ' %
                  len(self.clients))
        async with self.microscope_state_lock:
            if self.microscope_state:
                log.info('Sending microscope state to new client: %s :' %
                      self.microscope_state)
                await ws.send_json(self.microscope_state)

    async def remove_websocket_client(self, ws):
        async with self.clients_lock:
            # log.debug("number of clients before removing client: %s " %
            #       len(self.clients))
            self.clients.remove(ws)
            log.debug("number of clients after removing client: %s " %
                  len(self.clients))

    async def broadcast_to_websocket_clients(self, obj):
        """
        Converts obj to JSON string and sends the string to all connected websocket clients.
        :param obj: JSON-serializable object
        :return:
        """
        async with self.clients_lock:
            for ws in self.clients:
                # send object as JSON to websocket client
                await ws.send_json(obj)

    async def change_microscope_state(self, new_values):
        """
        Change a set of entries in the microscope state
        and notify websocket clients in case of changes
        :param changes: A dict with command-result values
        :type changes: dict
        :return:
        """
        changes = dict()
        async with self.microscope_state_lock:
            for command in new_values:
                new_result = new_values[command]
                if not command in self.microscope_state.keys():
                    # add new command/result to changes
                    changes[command] = new_result
                    # update value
                    self.microscope_state[command] = new_result
                elif new_result != self.microscope_state[command]:
                    # results differ: add new result to changes
                    changes[command] = new_result
                    # update value
                    self.microscope_state[command] = new_result
        if len(changes) > 0:
            log.info("microscope state changed: %s" % changes)
        if changes:
            await self.broadcast_to_websocket_clients(changes)

    def reset_microscope_state(self):
        self.microscope_state = dict()

    def run_server(self):
        log.info("Starting HTTP+websocket server with events under host=%s, port=%s" % (self.host, self.port))
        app = web.Application()
        # add routes for
        # - HTTP-GET/PUT, e.g. http://127.0.0.1:8080/v1/projection_mode
        # - websocket connection ws://127.0.0.1:8080/ws/v1
        app.add_routes([web.get('/ws/v1', self.websocket_handler_v1),  #
                        web.get(r'/v1/{name:.+}', self.http_get_handler_v1),
                        web.put(r'/v1/{name:.+}', self.http_put_handler_v1),
                        ])

        # set up aiohttp - like run_app, but non-blocking, 
        # see https://stackoverflow.com/questions/53465862/python-aiohttp-into-existing-event-loop
        runner = web.AppRunner(app)
        asyncio.ensure_future(runner.setup())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(runner.setup())
        site = web.TCPSite(runner)
        loop.run_until_complete(site.start())


class MicroscopeException(Exception):
    """
    Special exception class for returning HTTP status 204
    """
    def __init__(self, *args, **kw):
        super(MicroscopeException, self).__init__(*args, **kw)

class ArrayJSONEncoder(json.JSONEncoder):
    """
    Numpy array encoding JSON encoder
    """
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


class MicroscopeEventPublisher:
    """
    Periodically polls the microscope for a
    number of changes and forwards the result
    to the microscope state.
    :param microscope_server: The server instance
    :param sleep_time: The sleeping time between
            polling calls in seconds.
    :param polling_config: A configuration dict of
            methods and return types to poll.
            value is a tuple consisting of a conversion method
            (e.g. "float()") and a scaling factor
            (for int/float-types)
    """
    def __init__(self, microscope_server,
                 sleep_time, polling_config):
        self.microscope_server = microscope_server
        self.sleep_time = sleep_time
        self.polling_config = polling_config

        # the microscope state representation
        self.microscope_state = dict()
        # the method used for polling periodically
        self.polling_func = self.check_for_microscope_changes
        self.is_started = False
        self._task = None

    def start(self):
        log.debug("Starting server with events...")
        # reset microscope state
        self.microscope_server.reset_microscope_state()
        if not self.is_started:
            log.debug("Starting server now...")
            self.is_started = True
            # configure polling task to check for Temscript changes periodically:
            self._task = asyncio.ensure_future(self._run())

    def stop(self):
        log.info("Stopping server with events...")
        # reset microscope state
        self.microscope_server.reset_microscope_state()
        if self.is_started:
            self.is_started = False
            # Stop task and await it stopped:
            self._task.cancel()

    async def _run(self):
        log.info("Starting to poll for Temscripting changes with a polling time of %ss..." %
            self.sleep_time)
        while True:
            # sleep as configured for the instance
            await asyncio.sleep(self.sleep_time)
            # call polling function
            await self.polling_func()

    async def check_for_microscope_changes(self):
        #log.debug("checking for microscope changes...")
        try:
            changed = {}
            all_results = dict()
            for get_command in self.polling_config:
                try:
                    # execute get command
                    # (here: imply parameterless command)
                    result_raw = self.microscope_server.do_GET_V1(get_command,
                                                              None)
                    #log.debug("found %s=%s..." %
                    #      (get_command, result_raw))
                    casting_func = self.polling_config[get_command][0]
                    result = casting_func(result_raw)
                    # log.debug("Adding %s=%s to results..." %
                    #        (get_command, result))
                    all_results[get_command] = result
                except Exception as exc:
                    log.exception("TEMScripting method '{}' failed "
                        "while polling: %s" % (get_command, exc))
            await self.microscope_server.change_microscope_state(all_results)

        except Exception as exc:
            #traceback.print_exc()
            log.exception("Polling failed: %s" % exc)

def configure_server():
    """
    Configure logger, configuration file under %localappdata% and
    parse command line arguments
    ::return A tuple containing
            1. configuration dict
            2. the server port to use
    """
    # parse arguments
    parser = argparse.ArgumentParser(
        description='HTTP+Websocket Server for accessing Temscripting via web and sending change events via Websocket.')
    parser.add_argument('--port', type=int, action='store',
                        help='The HTTP+Websocket server port.')
    parser.add_argument('--pollsleep', type=float, action='store',
                        help='The Temscripting polling sleeping time (in seconds) between two polling actions.')
    # add arguments for logging: "loglevel", "logfile", "silent"
    logger.add_logger_arguments(parser)
    # parse arguments
    args = parser.parse_args()

    # load configuration file from %localappdata%
    config = server_config.Config("TemscriptingServer", local_appdata=True)
    config.loadConfigFile()
    log.info("Loaded configuration from file:\n%s", str(config))

    # check command line arguments vs. config file arguments:
    # - command line values win over config file values
    # - defaults will be added to config file in case they do not yet exist
    # - config file is saved at the end of the method in "%localappdata%" resp "~/.config"
    loglevel="INFO"
    if args.loglevel is not None:
        loglevel = args.loglevel
    else:
        if "loglevel" not in config:
            config["loglevel"] = "INFO"
        loglevel = config["loglevel"]

    logfile=None
    if args.logfile is not None:
        # command line argument for logfile wins over config file
        logfile = args.logfile
    else:
        # if logfile does not exist in config: keep value None!
        if "logfile" not in config:
            # TODO: better use appdirs library here
            config["logfile"] = "C:\\Temp\\TemscriptingServer.log"
        logfile = config["logfile"]

    silent=None
    if args.silent is not None:
        # command line argument for silent wins over config file
        silent = args.silent
    else:
        # if silent does not exist in config: keep value None!
        if "silent" not in config:
            # HTTP+Websocket server default port is 8080
            config["silent"] = True
        silent = config["silent"]

    # configure logger
    logger.configure_logger(log, loglevel, logfile, silent)
    log.info("Starting server with loglevel %s", loglevel)
    if logfile is not None and len(logfile)>0:
        log.info("Starting server with logfile %s", logfile)
    if silent is not None and silent:
        log.info("Starting server silently.")

    port=8080
    if args.port is not None:
        # command line argument for port wins over config file
        port = args.port
    else:
        if "port" not in config:
            # HTTP+Websocket server default port is 8080
            config["port"] = 8080
        port = config["port"]
    log.debug("Starting server on port: %s", port)

    polling_sleep=1.0
    if args.pollsleep is not None:
        # command line argument for port wins over config file
        polling_sleep = args.pollsleep
    else:
        if "pollsleep" not in config:
            config["pollsleep"] = 1.0
        polling_sleep = config["pollsleep"]
    log.debug("Starting server with polling sleep of %s s", polling_sleep)

    # save config file (containing defaults for new parameters)
    config.saveConfigFile()
    # return resulting values (command line arguments win over config file)
    return config,port,polling_sleep

if __name__ == '__main__':
    # configure logger, configuration file and parse command line arguments
    (config,port,polling_sleep) = configure_server()
    log.debug("configuration file=%s" % config)
    log.debug("port=%s" % config)
    log.debug("polling sleep=%ss" % polling_sleep)

    # define all TEMScripting methods which should be polled
    # during one polling event via the web server.
    # value is a tuple consisting of a conversion method
    # (e.g. "float()") and a scaling factor (for int/float)
    # for the result of the method
    tem_scripting_method_config = {
        # for meta data key 'condenser.mode'
        "instrument_mode_string": (str, 1),     # "TEM"/"STEM"
        "illumination_mode":      (int, 1),    # e.g., 0 ("NANOPROBE"), 1: ("MICROPROBE")
        "df_mode_string": (str, 1),             # e.g., "CARTESIAN", "OFF"
        "spot_size_index": (int, 1),            # e.g., 3
        "condenser_mode_string": (str, 1),      # e.g., "PROBE"
        "beam_blanked": (bool, 1),              # True, False
        # for meta data key 'electron_gun.voltage'
        "voltage": (float, 1),                  # e.g., "200"
        # for backend key 'microscope.elementValues.HTOffset'
        "voltage_offset": (float, 1),           # e.g., "0.1"
        # for meta data key "objective.mode -> projector.camera_length"
        "indicated_camera_length": (float, 1),  # e.g., "0.028999", in meters
        # for meta data key "objective.mode -> projector.magnification"
        "indicated_magnification": (float, 1),  # e.g., 200000.0
        # for meta data key "objective.mode -> projector.mode"
        "projection_mode_string": (str, 1),     # e.g., "SA"
        "projection_mode_type_string": (str, 1),# e.g., "IMAGING"
        # for meta data key "objective.mode -> scan_driver.magnification"
        "stem_magnification": (float, 1),       # e.g., "6000"
    }

    log.info("Using HTTP+Websocket port %s..." % port)

    # startup HTTP+Websocket server
    from temscript import Microscope
    #from microscope import Microscope
    microscope = Microscope()
    host="0.0.0.0"
    server = MicroscopeServerWithEvents(microscope=microscope,
                                        host=host, port=port)
    microscope_event_publisher = MicroscopeEventPublisher(server, polling_sleep,
                                        tem_scripting_method_config)
    # configure asyncio task for web server
    server.run_server()
    # configure asyncio task for polling temscript changes and
    # publishing them via websocket
    microscope_event_publisher.start()
    # start asyncio event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    finally:
        log.info("Stopping server.")
        microscope_event_publisher.stop()
        loop.stop()

