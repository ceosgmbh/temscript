from temscript import server_with_events
from temscript.null_microscope import NullMicroscope
from asyncio import get_event_loop

# to be started on the Titan microscope PC
print("Starting DUMMY temscripting Microscope HTTP Server with Websocket Events...")
try:
    # start remote server with events on localhost, port 8080
    microscope = NullMicroscope()

    temscripting_server = server_with_events.MicroscopeServerWithEvents(
        microscope=microscope, host="0.0.0.0", port=8080)
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
        # for meta data key "objective.mode -> projector.camera_length"
        "indicated_camera_length": (int, 1),    # e.g., "0", in meters (?)
        # for meta data key "objective.mode -> projector.magnification"
        "indicated_magnification": (float, 1),  # e.g., 200000.0
        # for meta data key "objective.mode -> projector.mode"
        "projection_mode_string": (str, 1),     # e.g., "SA"
        "projection_mode_type_string": (str, 1),# e.g., "IMAGING"
        # for meta data key "objective.mode -> scan_driver.magnification"
        "stem_magnification": (float, 1),       # e.g., "6000"
    }

    microscope_event_publisher = server_with_events.\
        MicroscopeEventPublisher(temscripting_server, 1.0,
                                 tem_scripting_method_config)
    try:
        microscope_event_publisher.start()
        temscripting_server.run_server()
    finally:
        microscope_event_publisher.stop()
except Exception as exc:
    print("Caught exception %s" % exc)
    raise exc

print("Done.")  