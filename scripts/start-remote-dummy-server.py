from temscript import server

# for testing the remote server without an actual Titan installation (i.e., on a PC different from the microscope PC)
print("Starting temscripting DUMMY Microscope Server...")
try:
    # start dummy server on localhost, port 8080
    temscripting_server = server.NullMicroscopeServer(("0.0.0.0", 8080), server.MicroscopeHandler)
    temscripting_server.serve_forever()
except Exception as exc:
    print("Caught exception %s" % exc)

print("Done.")  