from temscript import server_with_events
from temscript.null_microscope import NullMicroscope
from temscript.version import __version__
from asyncio import get_event_loop

import traceback

from functools import partial
from temscript import logger

# configure logger, configuration file (under %localappdata%) and parse command line arguments
(config, port, polling_sleep) = server_with_events.configure_server()
log = logger.getLoggerForModule("TemscriptingServer")
log.info("configuration read from file=%s" % config)
log.info("port=%s" % port)
log.info("polling sleep=%ss" % polling_sleep)

# to be started on the Titan microscope PC
log.info("Starting DUMMY temscripting Microscope HTTP Server with "
         "Websocket Events version for legacy Titan 6.x %s..." % __version__)
try:
    # start remote server with events on localhost with default port 8080
    microscope = NullMicroscope()

    temscripting_server = server_with_events.MicroscopeServerWithEvents(
        microscope=microscope, host="0.0.0.0", port=port)
    # define all TEMScripting methods which should be polled
    # during one polling event via the web server.
    # Here: Use only methods from the `Gun` interface and ignore `voltage_offset` resp. HT offset
    # value is a tuple consisting of a conversion method
    # (e.g. "float()") and a scaling factor (for int/float)
    # for the result of the method
    tem_scripting_method_config = {
        # for meta data key 'condenser.mode'
        "instrument_mode_string": (str, 1),     # "TEM"/"STEM"
        "illumination_mode":      (int, 1),     # e.g., 0 ("NANOPROBE"), 1: ("MICROPROBE")
        "df_mode_string": (str, 1),             # e.g., "CARTESIAN", "OFF"
        "spot_size_index": (int, 1),            # e.g., 3
        "condenser_mode_string": (str, 1),      # e.g., "PROBE"
        "beam_blanked": (bool, 1),              # True, False
        # for meta data key 'electron_gun.voltage'
        "voltage": (float, 1),                  # e.g., "200"
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

    microscope_event_publisher = server_with_events.\
        MicroscopeEventPublisher(temscripting_server, polling_sleep,
                                 tem_scripting_method_config)
    # configure asyncio task for web server
    temscripting_server.run_server()
    # configure asyncio task for polling temscript changes and
    # publishing them via websocket
    microscope_event_publisher.start()
    # start asyncio event loop
    loop = get_event_loop()
    try:
        loop.run_forever()
    finally:
        print("Stopping server.")
        microscope_event_publisher.stop()
        loop.stop()

except Exception as exc:
    log.exception("Caught exception %s" % exc)
    #print(traceback.format_exc())
    #wait = input("Press Enter to exit server.")

log.info("Done.")