"""Module containing logging classes and functions
"""

import os
import datetime

_WRITE_FUNCTION = None
_DEBUG = False
_LOG_FILE = None


def initialize_logger():
    global _LOG_FILE
    if not os.path.exists('logs'):
        os.mkdir('logs')
    _LOG_FILE = open(os.path.join('logs', 'installSynApps_{}.log'.format(datetime.datetime.now())), 'w')

def close_logger():
    global _LOG_FILE
    if _LOG_FILE is not None:
        _LOG_FILE.close()


def toggle_debug_logging():
    global _DEBUG
    _DEBUG = not _DEBUG


def assign_write_function(write_function):
    global _WRITE_FUNCTION
    _WRITE_FUNCTION = write_function


def debug(text):
    global _DEBUG
    if _DEBUG:
        write(text)


def write(text):
    global _DEBUG
    global _WRITE_FUNCTION

    if not _DEBUG:
        final_text = '{}\n'.format(text)
    else:
        final_text = '{} - {}\n'.format(datetime.datetime.now(), text)

    log_write(final_text)

    if _WRITE_FUNCTION is not None:
        _WRITE_FUNCTION(final_text)


def log_write(text):
    global _LOG_FILE
    if _LOG_FILE is not None:
        _LOG_FILE.write(text)


def log_write_subprocess_call(out, err):
    if out is not None:
        log_write(out.decode())
    if err is not None:
        log_write(out, err)
