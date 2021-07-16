from temscript import server

# to be started on the Titan microscope PC
print("Starting temscripting Microscope HTTP Server...")
try:
    # start dummy server on localhost, port 8080
    temscripting_server = server.MicroscopeServer(("0.0.0.0", 8080), server.MicroscopeHandler)
    temscripting_server.serve_forever()
except Exception as exc:
    print("Caught exception %s" % exc)

print("Done.")  