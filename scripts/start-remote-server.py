from temscript import server

# to be started on the Titan microscope PC
print("Starting temscripting Microscope REST Server...")
try:
    # start dummy server on localhost, port 8080
    temscripting_server = server.MicroscopeServer(("127.0.0.1", 8080), server.MicroscopeHandler)
    temscripting_server.serve_forever()
except Exception as exc:
    print("Caught exception %s" % exc)

print("Done.")  