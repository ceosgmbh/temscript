import json
import os
import sys


class Config(dict):

    def __init__(self, moduleName, local_appdata=False):
        """Create a new Config dict.

        :param moduleName: name of the configuration file
        :param local_appdata: Windows only:
            False: ../AppData/Roaming
            True: ../AppData/Local
        """
        self.moduleName = moduleName

        # https://installmate.com/support/im9/using/symbols/functions/csidls.htm
        if local_appdata:
            csidl = 28  # CSIDL_LOCAL_APPDATA
        else:
            csidl = 26  # CSIDL_APPDATA

        self._configFolder = self._getConfigFolder(csidl)

        data = self.loadConfigFile()
        dict.__init__(self, data)

    def loadConfigFile(self):
        configFile = os.path.join(self._configFolder,
                                  '%s.json' % self.moduleName)

        if not os.path.exists(configFile):
            return {}
        try:
            f = open(configFile, 'r')
            import json
            config = json.load(f)
        except (IOError, ValueError) as error:
            sys.stderr.write(
                'Unable to load configuration from %s: %s\n' %
                (configFile, str(error)))
            return {}

        return config

    def saveConfigFile(self):
        folder = self._configFolder
        if not os.path.isdir(folder):
            os.mkdir(folder)
        configFile = os.path.join(folder, '%s.json' % self.moduleName)
        if sys.version_info < (3, ):
            with open(configFile, 'w') as f:
                return json.dump(self, f, encoding='UTF-8')
        else:
            with open(configFile, 'w', encoding='UTF-8') as f:
                return json.dump(self, f)

    @staticmethod
    def _getConfigFolder(csidl):
        if os.name != 'posix':
            # pylint: disable=import-error
            import ctypes.wintypes

            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(0, csidl, 0, 0, buf)

            configFolder = buf.value
        else:
            configFolder = os.path.expanduser(
                os.environ.get('XDG_CONFIG_HOME', '~/.config'))
            if not os.path.isdir(configFolder):
                os.mkdir(configFolder)

        return os.path.join(configFolder, 'CEOS')
