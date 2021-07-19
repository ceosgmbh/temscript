from temscript import server_with_events

# to be started on the Titan microscope PC
print("Starting temscripting Microscope HTTP Server with Websocket...")
try:
    # start dummy server on localhost, port 8080
    temscripting_server = server_with_events.MicroscopeServerWithEvents(host="0.0.0.0", port=8080)
    temscripting_server.run_server()
except Exception as exc:
    print("Caught exception %s" % exc)

print("Done.")  