from temscript import server

print("Starting temscripting DUMMY Microscope Server...")
# for testing without Titan installation
try:
    # start dummy server on localhost, port 8080
    temscripting_server = server.NullMicroscopeServer(("127.0.0.1", 8080), server.MicroscopeHandler)
    temscripting_server.serve_forever()
except Exception as exc:
    print("Caught exception %s" % exc)

print("Done.")  