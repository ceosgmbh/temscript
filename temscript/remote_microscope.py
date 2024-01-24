#!/usr/bin/python
from __future__ import division, print_function
import numpy as np
import json
import socket

# Get imports from library
try:
    # Python 3.X
    from http.client import HTTPConnection
    from urllib.parse import urlencode
    from io import BytesIO
except ImportError:
    # Python 2.X
    from httplib import HTTPConnection
    from urllib import urlencode
    from cStringIO import StringIO as BytesIO


class RemoteMicroscope(object):
    """
    Microscope-like class, which connects to a remote microscope server.

    Use the ``temscript-server`` command line script to run a microscope server.

    :param address: (host, port) combination for the remote microscope.
    :param transport: Underlying transport protocol, either 'JSON' (default) or 'pickle'
    """
    def __init__(self, address, transport=None, timeout=None):
        self.address = address
        self.timeout = timeout
        self._conn = None
        if transport is None:
            transport = "JSON"
        if transport == "JSON":
            self.accepted_content = ["application/json"]
        elif transport == "PICKLE":
            self.accepted_content = ["application/python-pickle"]
        else:
            raise ValueError("Unknown transport protocol.")

    def _request(self, method, endpoint, query={}, body=None, headers={}, accepted_response=[200]):
        # Make connection
        if self._conn is None:
            self._conn = HTTPConnection(self.address[0], self.address[1], timeout=self.timeout)

        # Create request
        if len(query) > 0:
            url = "%s?%s" % (endpoint, urlencode(query))
        else:
            url = endpoint
        headers = dict(headers)
        if "Accept" not in headers:
            headers["Accept"] = ",".join(self.accepted_content)
        if "Accept-Encoding" not in headers:
            headers["Accept-Encoding"] = "gzip"
        self._conn.request(method, url, body, headers)

        # Get response
        try:
            response = self._conn.getresponse()
        except socket.timeout:
            self._conn.close()
            self._conn = None
            raise

        body = response.read()
        if response.status not in accepted_response:
            raise ValueError("Failed remote call: %d, %s" % (response.status, response.reason))
        if response.status == 204:
            return response, body

        # Decode response
        content_type = response.getheader("Content-Type")
        if content_type not in self.accepted_content:
            raise ValueError("Unexpected response type: {}".format(content_type))
        if response.getheader("Content-Encoding") == "gzip":
            import zlib
            body = zlib.decompress(body, 16 + zlib.MAX_WBITS)
        if content_type == "application/json":
            body = json.loads(body.decode("utf-8"))
        elif content_type == "application/python-pickle":
            import pickle
            body = pickle.loads(body)
        else:
            raise ValueError("Unsupported response type: %s", content_type)
        return response, body

    def get_family(self):
        response, body = self._request("GET", "/v1/family")
        return body

    def get_microscope_id(self):
        response, body = self._request("GET", "/v1/microscope_id")
        return body

    def get_version(self):
        response, body = self._request("GET", "/v1/version")
        return body

    def get_voltage(self):
        response, body = self._request("GET", "/v1/voltage")
        return body

    def get_voltage_offset(self):
        response, body = self._request("GET", "/v1/voltage_offset")
        return body

    def set_voltage_offset(self, voltage_offset_value):
        content = json.dumps(voltage_offset_value).encode("utf-8")
        self._request("PUT", "/v1/voltage_offset", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_stage_holder(self):
        response, body = self._request("GET", "/v1/stage_holder")
        return body

    def get_stage_status(self):
        response, body = self._request("GET", "/v1/stage_status")
        return body

    def get_stage_limits(self):
        response, body = self._request("GET", "/v1/stage_limits")
        return body

    def get_stage_position(self):
        response, body = self._request("GET", "/v1/stage_position")
        return body

    def set_stage_position(self, pos=None, method=None, **kw):
        pos = dict(pos, **kw) if pos is not None else dict(**kw)
        if method is not None:
            pos["method"] = method
        elif "method" in pos:
            del pos["method"]
        content = json.dumps(pos).encode("utf-8")
        self._request("PUT", "/v1/stage_position", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_vacuum(self):
        response, body = self._request("GET", "/v1/vacuum")
        return body

    def get_detectors(self):
        response, body = self._request("GET", "/v1/detectors")
        return body

    def get_detector_param(self, name):
        response, body = self._request("GET", "/v1/detector_param/" + name)
        return body

    def set_detector_param(self, name, param):
        content = json.dumps(param).encode("utf-8")
        self._request("PUT", "/v1/detector_param/" + name, body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_image_shift(self):
        response, body = self._request("GET", "/v1/image_shift")
        return body

    def set_image_shift(self, pos):
        content = json.dumps(tuple(pos)).encode("utf-8")
        self._request("PUT", "/v1/image_shift", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_beam_shift(self):
        response, body = self._request("GET", "/v1/beam_shift")
        return body

    def set_beam_shift(self, pos):
        content = json.dumps(tuple(pos)).encode("utf-8")
        self._request("PUT", "/v1/beam_shift", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_beam_tilt(self):
        response, body = self._request("GET", "/v1/beam_tilt")
        return body

    def set_beam_tilt(self, pos):
        content = json.dumps(tuple(pos)).encode("utf-8")
        self._request("PUT", "/v1/beam_tilt", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_df_mode(self):
        response, body = self._request("GET", "/v1/df_mode")
        return body

    def get_df_mode_string(self):
        response, body = self._request("GET", "/v1/df_mode_string")
        return body

    def set_df_mode(self, df_mode):
        content = json.dumps(df_mode).encode("utf-8")
        self._request("PUT", "/v1/df_mode", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_beam_blanked(self):
        response, body = self._request("GET", "/v1/beam_blanked")
        return body

    def set_beam_blanked(self, beam_blanked):
        content = json.dumps(beam_blanked).encode("utf-8")
        self._request("PUT", "/v1/beam_blanked", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_spot_size_index(self):
        response, body = self._request("GET", "/v1/spot_size_index")
        return body

    allowed_types = {"INT8", "INT16", "INT32", "INT64", "UINT8", "UINT16", "UINT32", "UINT64", "FLOAT32", "FLOAT64"}
    allowed_endianness = {"LITTLE", "BIG"}

    def acquire(self, *detectors):
        query = [("detectors", det) for det in detectors]
        response, body = self._request("GET", "/v1/acquire", query=query)
        if response.getheader("Content-Type") == "application/json":
            # Unpack array
            import sys
            import base64
            endianness = sys.byteorder.upper()
            result = {}
            for k, v in body.items():
                shape = int(v["height"]), int(v["width"])
                if v["type"] not in self.allowed_types:
                    raise ValueError("Unsupported array type in JSON stream: %s" % str(v["type"]))
                if v["endianness"] not in self.allowed_endianness:
                    raise ValueError("Unsupported endianness in JSON stream: %s" % str(v["endianness"]))
                dtype = np.dtype(v["type"].lower())
                if v["encoding"] == "BASE64":
                    data = base64.b64decode(v["data"])
                else:
                    raise ValueError("Unsupported encoding of array in JSON stream: %s" % str(v["encoding"]))
                data = np.frombuffer(data, dtype=dtype).reshape(*shape)
                if v["endianness"] != endianness:
                    data = data.byteswap()
                result[k] = data
            body = result
        return body

    def normalize(self, mode="ALL"):
        mode = str(mode)
        content = json.dumps(mode).encode("utf-8")
        self._request("PUT", "/v1/acquire", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_instrument_mode(self):
        response, body = self._request("GET", "/v1/instrument_mode")
        return body

    def get_instrument_mode_string(self):
        response, body = self._request("GET", "/v1/instrument_mode_string")
        return body


    def get_projection_sub_mode(self):
        response, body = self._request("GET", "/v1/projection_sub_mode")
        return body

    def get_projection_mode(self):
        response, body = self._request("GET", "/v1/projection_mode")
        return body

    def set_projection_mode(self, mode):
        content = json.dumps(mode).encode("utf-8")
        self._request("PUT", "/v1/projection_mode", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_projection_mode_string(self):
        response, body = self._request("GET", "/v1/projection_mode_string")
        return body

    def get_projection_mode_type_string(self):
        response, body = self._request("GET", "/v1/projection_mode_type_string")
        return body

    def get_lens_program(self):
        response, body = self._request("GET", "/v1/lens_program")
        return body

    def get_lens_program_string(self):
        response, body = self._request("GET", "/v1/lens_program_string")
        return body

    def set_lens_program(self, lens_program):
        content = json.dumps(lens_program).encode("utf-8")
        self._request("PUT", "/v1/lens_program", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_illumination_mode(self):
        response, body = self._request("GET", "/v1/illumination_mode")
        return body

    def get_illumination_mode_string(self):
        response, body = self._request("GET", "/v1/illumination_mode_string")
        return body

    def get_illuminated_area(self):
        response, body = self._request("GET", "/v1/illuminated_area")
        return body

    def set_illuminated_area(self, illuminated_area):
        content = json.dumps(illuminated_area).encode("utf-8")
        self._request("PUT", "/v1/illuminated_area", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_convergence_angle(self):
        response, body = self._request("GET", "/v1/convergence_angle")
        return body

    def get_condenser_mode(self):
        response, body = self._request("GET", "/v1/condenser_mode")
        return body

    def get_condenser_mode_string(self):
        response, body = self._request("GET", "/v1/condenser_mode_string")
        return body

    def get_magnification_index(self):
        response, body = self._request("GET", "/v1/magnification_index")
        return body

    def set_magnification_index(self, index):
        content = json.dumps(index).encode("utf-8")
        self._request("PUT", "/v1/magnification_index", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_stem_magnification(self):
        response, body = self._request("GET", "/v1/stem_magnification")
        return body

    def set_stem_magnification(self, stem_mag):
        content = json.dumps(stem_mag).encode("utf-8")
        self._request("PUT", "/v1/stem_magnification", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_indicated_camera_length(self):
        response, body = self._request("GET", "/v1/indicated_camera_length")
        return body

    def get_indicated_magnification(self):
        response, body = self._request("GET", "/v1/indicated_magnification")
        return body

    def get_defocus(self):
        response, body = self._request("GET", "/v1/defocus")
        return body

    def set_defocus(self, value):
        content = json.dumps(value).encode("utf-8")
        self._request("PUT", "/v1/defocus", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_probe_defocus(self):
        response, body = self._request("GET", "/v1/probe_defocus")
        return body

    def set_probe_defocus(self, probe_defocus):
        content = json.dumps(probe_defocus).encode("utf-8")
        self._request("PUT", "/v1/probe_defocus", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_objective_excitation(self):
        response, body = self._request("GET", "/v1/objective_excitation")
        return body

    def get_intensity(self):
        response, body = self._request("GET", "/v1/intensity")
        return body

    def set_intensity(self, value):
        content = json.dumps(value).encode("utf-8")
        self._request("PUT", "/v1/intensity", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_condenser_stigmator(self):
        response, body = self._request("GET", "/v1/condenser_stigmator")
        return body

    def set_condenser_stigmator(self, value):
        content = json.dumps(tuple(value)).encode("utf-8")
        self._request("PUT", "/v1/condenser_stigmator", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_objective_stigmator(self):
        response, body = self._request("GET", "/v1/objective_stigmator")
        return body

    def set_objective_stigmator(self, value):
        content = json.dumps(tuple(value)).encode("utf-8")
        self._request("PUT", "/v1/objective_stigmator", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_diffraction_shift(self):
        response, body = self._request("GET", "/v1/diffraction_shift")
        return body

    def set_diffraction_shift(self, value):
        content = json.dumps(tuple(value)).encode("utf-8")
        self._request("PUT", "/v1/diffraction_shift", body=content, accepted_response=[200, 204],
                      headers={"Content-Type": "application/json"})

    def get_optics_state(self):
        response, body = self._request("GET", "/v1/optics_state")
        return body


if __name__ == '__main__':
    SERVER_PORT = 8080
    #SERVER_HOST = 'localhost'
    SERVER_HOST = '192.168.99.10'
    TRANSPORT = "JSON" # "PICKLE"
    client = RemoteMicroscope((SERVER_HOST, SERVER_PORT), transport=TRANSPORT)

    if 0:
        print("TEST-1", client.get_test())
        client.set_test({"EINS": 1, "ZWEI": 2.0, "DREI": "xxx", "VIER": [0, 1, 2, 3]})
        print("TEST-2", client.get_test())

    if 1:
        print("FAMILY", client.get_family())
        print("VACUUM", client.get_vacuum())
        print("STAGE_HOLDER", client.get_stage_holder())
        print("STAGE_STATUS", client.get_stage_status())
        print("STAGE_LIMITS", client.get_stage_limits())
        print("STAGE_POSITION", client.get_stage_position())
        print("DETECTORS", client.get_detectors())

    if 1:
        param = client.get_detector_param("CCD")
        print("DETECTOR_PARAM(CCD)-1", param)
        exposure = 1.0 if param["exposure(s)"] != 1.0 else 1.0 / param["exposure(s)"]
        client.set_detector_param("CCD", {"exposure(s)": exposure})
        print("DETECTOR_PARAM(CCD)-2", client.get_detector_param("CCD"))

        images = client.acquire("CCD")
        print("ACQUIRE(CCD)-ARRAY", images["CCD"].shape, images["CCD"].dtype)

        import matplotlib.pyplot as plt

        plt.imshow(images["CCD"], cmap="gray")
        plt.show()

    if 0:
        pos = client.get_stage_position()
        new_x = 10e-6 if pos['x'] < 0 else -10e-6
        client.set_stage_position({'x': new_x})
        for n in range(20):
            print(client.get_stage_status(), client.get_stage_position())
