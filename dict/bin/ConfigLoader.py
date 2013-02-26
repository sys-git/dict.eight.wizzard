'''
Created on 25 Feb 2013

@author: francis
'''

from ConfigParser import ConfigParser
from dict.bin import FileCodec
from dict.bin.WellBehavedOptionParser import WellBehavedOptionParser
import copy
import os
import sys
import tempfile

class ConfigLoader(object):
    DEFAULT_REFRESH_PERIOD = { "option":"-r",
                               "longOption":"--refresh-period",
                               "dest":"defaultRefreshPeriod",
                               "help":'Default refresh period, default=20 seconds',
                               "type":int,
                               "file":{"section":"program", "option":"defaultRefreshPeriod"},
                               "default":20}
    NO_SOUND_ON_EVENT = { "option":"-n",
                           "longOption":"--no-sound-on-event",
                           "dest":"noSoundOnEvent",
                           "help":'No sounds when an event occurs, default=False',
                           "file":{"section":"program", "option":"noSoundOnEvent"},
                           "default":False}
    HISTORY_FILENAME = { "longOption":"--history-filename",
                       "dest":"historyFilename",
                       "help":'No sounds when an event occurs, default="output/history.txt"',
                       "file":{"section":"program", "option":"historyFilename"},
                       "default":"output/history.txt"}
    DEFAULT_BOMBOUT = { "longOption":"--default-bombout",
                           "dest":"defaultBombout",
                           "help":'Bombout by default on error, default=True',
                           "file":{"section":"program", "option":"defaultBombout"},
                           "default":True}
    DEFAULT_SINGLEREFRESH = { "longOption":"--default-single-refresh",
                           "dest":"defaultSingleRefresh",
                           "help":'Bombout by default on error, default=0',
                           "file":{"section":"program", "option":"defaultSingleRefresh"},
                           "type":"int",
                           "default":0}
    DISABLE_ADAPTIVE_SOUND = {"longOption":"--disable-adaptive-sound",
                               "dest":"disableAdaptiveSound",
                               "help":'Disable Adaptive Sound, default=False',
                               "file":{"section":"program", "option":"disableAdaptiveSound"},
                               "default":False}
    DEFAULT_MIN_REFRESH_PERIOD = {"longOption":"--default-min-refresh-period",
                               "dest":"defaultMinimumRefreshPeriod",
                               "help":'Default minimum refresh period, default=0',
                               "file":{"section":"program", "option":"defaultMinimumRefreshPeriod"},
                               "type":"int",
                               "default":7}
    DEFAULT_MAX_REFRESH_PERIOD = {"longOption":"--default-max-refresh-period",
                               "dest":"defaultMaximumRefreshPeriod",
                               "help":'Default minimum refresh period, default=3600',
                               "file":{"section":"program", "option":"defaultMaximumRefreshPeriod"},
                               "type":"int",
                               "default":3600}
    DEFAULT_NOTIFICATION_SEPERATOR = {"longOption":"--default-notification-seperator",
                                   "dest":"defaultNotificationSeperator",
                                   "help":'Default notification seperator, default="\n\n"',
                                   "file":{"section":"program", "option":"defaultNotificationSeperator"},
                                   "default":"\n\n"}
    DEFAULT_LOGIN_RETRY_TIMEOUT = {"longOption":"--default-login-retry-timeout",
                                   "dest":"defaultLoginRetryTimeout",
                                   "help":'Default login retry timeout, default=60',
                                   "file":{"section":"program", "option":"defaultLoginRetryTimeout"},
                                   "type":"int",
                                   "default":60}
    DEFAULT_WEBSITE_USER = { "option":"-u",
                           "longOption":"--website-username",
                           "dest":"defaultWebsiteUsername",
                           "help":'Username, default=""',
                           "file":{"section":"user", "option":"user"},
                           "default":""}
    DEFAULT_WEBSITE_PASS = { "option":"-p",
                           "longOption":"--website-password",
                           "dest":"defaultWebsitePassword",
                           "help":'Password, default=""',
                           "file":{"section":"user", "option":"pass"},
                           "default":""}
    DEFAULT_WEBSITE_HOST = { "option":"-a",
                           "longOption":"--default-website-address",
                           "dest":"defaultWebsiteAddress",
                           "help":'Website address (eg: https://www.xyz.com), default=""',
                           "file":{"section":"user", "option":"host"},
                           "default":""}
    ENC_OPTIONS_FILENAME = { "option":"-o",
                           "longOption":"--encrypted-options-filename",
                           "dest":"options",
                           "help":'Encrypted options file (eg: /options.bin), default=None',
                           "file":{},
                           "default":None}
    ENC_OPTIONS_KEY = { "option":"-k",
                       "longOption":"--encrypted-options-key",
                       "dest":"optionsKey",
                       "help":'Encrypted options file key (eg: pa88w0rd), default="pa88w0rd"',
                       "file":{},
                       "default":"pa88w0rd"}
    SOUNDS_ERROR = {"longOption":"--sounds-error",
                   "dest":"soundsError",
                   "help":'Error sound, default"=media/error.wav"',
                   "file":{"section":"sounds", "option":"error"},
                   "default":"media/error.wav"}
    SOUNDS_NEW = {"longOption":"--sounds-new",
                   "dest":"New sound, default'=media/error.wav'",
                   "file":{"section":"sounds", "option":"new"},
                   "default":"media/new_task.wav"}
    SOUNDS_RUNNING = {"longOption":"--sounds-running",
                   "dest":"soundsRunning",
                   "help":'Running sound, default"=media/running.wav"',
                   "file":{"section":"sounds", "option":"running"},
                   "default":"media/running.wav"}
    SOUNDS_ENDING = {"longOption":"--sounds-ending",
                   "dest":"soundsEnding",
                   "help":'Ending sound, default"=media/ending.wav"',
                   "file":{"section":"sounds", "option":"ending"},
                   "default":"media/ending.wav"}
    ENABLE_DEBUG = {"longOption":"--debug-enable",
                   "dest":"enableDebug",
                   "help":'Enable debug, default=False',
                   "file":{"section":"debug", "option":"enable"},
                   "default":False}
    NO_PRINT_TO_FILE = {"longOption":"--no-print-to-file",
                   "dest":"noPrintToFile",
                   "help":'No print to file, default=False',
                   "file":{"section":"debug", "option":"noPrintToFile"},
                   "default":False}

    def __init__(self, args=[], exitOnError=True):
        options, args = ConfigLoader._parse(args, exitOnError)
        self._options = options
        self._args = args
        #    Now override with values from the file:
        filename = self._options["options"]
        if filename!=None:
            filename = os.path.realpath(filename)
            key = self._options["optionsKey"]
            self._options.update(ConfigLoader._load(filename, key))
    def getOptions(self):
        return self._options
    def getArgs(self):
        return self._args
    options = property(getOptions)
    args = property(getArgs)
    @staticmethod
    def _parse(args, exitOnError):
        parser = WellBehavedOptionParser(description='SAS SASCreator - cmdline parser', exitOnError=exitOnError)
        for attr in dir(ConfigLoader):
            if not attr.startswith("_") and attr[0].isupper():
                kwargs = copy.deepcopy(getattr(ConfigLoader, attr))
                args_ = []
                try:    args_.append(kwargs.pop("option"))
                except: pass
                try:    args_.append(kwargs.pop("longOption"))
                except: pass
                try:    kwargs.pop("file")
                except: pass
                args_ = tuple(args_)
                parser.add_option(*args_, **kwargs)
        (options, args) = parser.parse_args(args)
        return vars(options), args
    @staticmethod
    def _load(optionsFile, key):
        opts = {}
        config = ConfigParser()
        tmpFile = tempfile.mkstemp()
        os.close(tmpFile[0])
        try:
            FileCodec.work(["-d", optionsFile, "-k", key, "-o", tmpFile[1]])
            config.readfp(open(tmpFile[1]))
        except Exception, _e:
            config.readfp(optionsFile)
        os.remove(tmpFile[1])
        for section in config.sections():
            for option in config.options(section):
                value = config.get(section, option)
                try:
                    key = ConfigLoader._getKey(section, option)
                except Exception, _e:
                    key = ConfigLoader._getKey(section, option)
                opts[key] = value
        return opts
    @staticmethod
    def _getKey(section, option):
        for attr in dir(ConfigLoader):
            if not attr.startswith("_") and attr[0].isupper():
                kwargs = copy.deepcopy(getattr(ConfigLoader, attr))
                f =  kwargs.get("file", None)
                if f!=None:
                    try:
                        if f["section"].lower()==section.lower() and f["option"].lower()==option.lower():
                            return kwargs["dest"]
                    except:
                        pass
        raise ValueError("[%(S)s]:[%(O)s]"%{"S":section, "O":option})

if __name__ == '__main__':
    cl = ConfigLoader(sys.argv[1:])
    print cl.options
