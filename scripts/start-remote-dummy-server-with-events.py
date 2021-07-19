from temscript import server_with_events
from temscript.microscope import Microscope
from temscript.null_microscope import NullMicroscope

# to be started on the Titan microscope PC
print("Starting DUMMY temscripting Microscope HTTP Server with Websocket Events...")
try:
    # start remote server with events on localhost, port 8080
    microscope = NullMicroscope()
    temscripting_server = server_with_events.MicroscopeServerWithEvents(
        microscope=microscope, host="0.0.0.0", port=8080)
    temscripting_server.run_server()
except Exception as exc:
    print("Caught exception %s" % exc)

print("Done.")  