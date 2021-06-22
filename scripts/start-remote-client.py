from temscript.remote_microscope import RemoteMicroscope
from temscript.microscope import DarkFieldMode

print("Starting Temscripting Microscope HTTP Client...")
#try:
SERVER_PORT = 8080
#SERVER_HOST = 'localhost'
SERVER_HOST = '127.0.0.1'
TRANSPORT = "JSON" # "PICKLE"
client = RemoteMicroscope((SERVER_HOST, SERVER_PORT), transport=TRANSPORT)

print("projection_mode=%s" % client.get_projection_mode())
print("projection_sub_mode=%s" % client.get_projection_sub_mode())
print("projection_mode_string=%s" % client.get_projection_mode_string())
print("magnification_index=%s" % client.get_magnification_index())
print("indicated_magnification=%s" % client.get_indicated_magnification())
print("indicated_camera_length=%s" % client.get_indicated_camera_length())
# response, body = client._request("GET", "/v1/stem_magnification")
# print("stem_magnification=%s" % body)
print("stem_magnification=%s" % client.get_stem_magnification())
print("Changing stem_magnification...")
client.set_stem_magnification(6000.0)
print("stem_magnification2=%s" % client.get_stem_magnification())
print("voltage=%sKV" % client.get_voltage())
print("df_mode=%s" % client.get_df_mode())
print("Changing df_mode...")
client.set_df_mode(1)
print("df_mode=%s" % client.get_df_mode())
print("stem_magnification2=%s" % client.get_stem_magnification())
print("illumination_mode=%s" % client.get_illumination_mode())
print("spot_size_index=%s" % client.get_spot_size_index())
print("condenser_mode=%s" % client.get_condenser_mode())
print("beam_blanked=%s" % client.get_beam_blanked())
print("Changing beam_blanked...")
client.set_beam_blanked(True)
print("beam_blanked=%s" % client.get_beam_blanked())
print("family=%s" % client.get_family())
print("stage_holder=%s" % client.get_stage_holder())
print("stage_position=%s" % client.get_stage_position())

# except Exception as exc:
#     print("Caught exception %s" % exc)

 
print("Done.")