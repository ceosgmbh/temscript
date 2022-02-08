"""
Collection of small function that do not fit elsewhere.
"""
import logging
from logging.handlers import RotatingFileHandler

fmt = logging.Formatter('%(asctime)s %(levelname)s %(process)d#%(thread)d %(module)s:%(lineno)d %(message)s')
std = logging.StreamHandler()

LOGLEVEL= { 'CRITICAL': logging.CRITICAL,
            'ERROR': logging.ERROR,
            'WARNING': logging.WARNING,
            'INFO': logging.INFO,
            'DEBUG': logging.DEBUG }

def add_logger_arguments(parser):
    parser.add_argument('--silent', action='store', help='suppress logging to console')
    parser.add_argument('--logfile', action='store', type=str, help='Log to file', default=None)
    parser.add_argument('--loglevel', action='store', choices=LOGLEVEL.keys(), default=None,
                        help='Select log level (default: INFO)')

def configure_logger(log, loglevel, logfile, silent):
    log.setLevel(LOGLEVEL[loglevel])

    if silent is not None and not silent:
        std.setFormatter(fmt)
        log.addHandler(std)
    if logfile is not None:

        def modify_name(name):
            toks = name.split('.')
            name = '.'.join(toks[:-2]+[toks[-1],toks[-2]])
            return name

        hdl = RotatingFileHandler(filename=logfile, maxBytes=1000000,
                                          backupCount=3)
        hdl.setFormatter(fmt)
        hdl.namer = modify_name
        log.addHandler(hdl)

def getLoggerForModule(moduleName):
    """
    Create a logger instance for given module name.

    :param moduleName: name of the module, typically __name__
    :returns: a logger instance
    """
    startIndex = 0
    endIndex = len(moduleName)
    # maximum 25 chars
    if startIndex+25 < endIndex:
        endIndex = startIndex+25

    orgLoggerClass = logging.getLoggerClass()
    if logging.Logger is orgLoggerClass:
        try:
            logger = logging.getLogger(moduleName[startIndex:endIndex])
        finally:
            logging.setLoggerClass(orgLoggerClass)
    else:
        logger = logging.getLogger(moduleName[startIndex:endIndex])

    return logger

