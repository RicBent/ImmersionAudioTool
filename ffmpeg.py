import os
import subprocess
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


_ffmpeg = None


def try_ffmpeg_path(path):
    try:
        from subprocess import DEVNULL
    except ImportError:
        DEVNULL = os.open(os.devnull, os.O_RDWR)

    try:
        output = subprocess.check_output([path, '-version'], stdin=DEVNULL, stderr=DEVNULL)
        if not output.startswith(b'ffmpeg'):
            return False
    except Exception as e:
        QMessageBox.information(None, '', path + '\n\n' + str(e))
        return False
    return True


def init():

    global _ffmpeg

    settings = QSettings()
    path = settings.value('ffmpeg_path', 'ffmpeg')

    if try_ffmpeg_path(path):
        _ffmpeg = path
        return True

    while True:
        r = QMessageBox.information(None, '', 'ffmpeg was not found. Please select a path to ffmpeg.', QMessageBox.Ok | QMessageBox.Cancel)
        if r != QMessageBox.Ok:
            return False

        path = QFileDialog.getOpenFileName(None, 'Select ffmpeg')[0]
        if not path:
            return False

        if not try_ffmpeg_path(path):
            continue
        
        _ffmpeg = path
        settings.setValue('ffmpeg_path', path)

        return True


def call(*args):

    global _ffmpeg

    if _ffmpeg is None:
        return -1

    call_args = [_ffmpeg] + list(args)

    return subprocess.call(call_args, shell=True)
