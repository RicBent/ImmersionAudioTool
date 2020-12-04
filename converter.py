import os
from collections import namedtuple
import tempfile
import subprocess
import eyed3
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import subtitles
import ffmpeg


Job = namedtuple('Job', 'media_file subtitle_file output_file')
Options = namedtuple('Options', 'join_secs pre_pad post_pad')
Metadata = namedtuple('Metadata', 'album album_art')


class ConverterThread(QThread):

    progress_update = pyqtSignal(object)

    def __init__(self, jobs, options, metadata, parent=None):
        super(ConverterThread, self).__init__(parent)
        self.jobs = jobs
        self.options = options
        self.metadata = metadata

    def run(self):

        num_jobs = len(self.jobs)

        album_art_data = None
        album_art_mime = None
        
        if self.metadata.album_art is not None:
            img_mime_types = {
                'png':  'image/png',
                'jpeg': 'image/jpeg',
                'jpg':  'image/jpeg',
            }

            extension_i = self.metadata.album_art.rfind('.')

            if extension_i > 0:
                extension = self.metadata.album_art[extension_i+1:].lower()
                if extension in img_mime_types:
                    album_art_file = open(self.metadata.album_art, 'rb')
                    album_art_data = album_art_file.read()
                    album_art_file.close()
                    album_art_mime = img_mime_types[extension]

        for job_idx, job in enumerate(self.jobs):
            with tempfile.TemporaryDirectory('iat') as tmp_path:
                subs = subtitles.parse_file(job.subtitle_file)

                parts = []

                for s in subs:
                    parts.append((s.start, s.end))    # todo: filter out useless stuff

                i = 1
                while i < len(parts):
                    last_part = parts[i-1]
                    curr_part = parts[i]

                    delta = curr_part[0] - last_part[1]

                    if delta <= self.options.join_secs:
                        parts[i-1] = (last_part[0], curr_part[1])
                        del parts[i]
                    else:
                        i += 1

                part_list_path = tmp_path + '/part_list.txt'
                part_list_f = open(part_list_path, 'w')

                num_parts = len(parts)

                for (i, (start, end)) in enumerate(parts):
                    print(F'[{job_idx+1}/{num_jobs}] ({i+1}/{num_parts}) {subtitles.secs_to_strtime(start)} {subtitles.secs_to_strtime(end)}')

                    progress = 0
                    if job_idx > 0:
                        progress += job_idx / num_jobs
                    if i > 0:
                        progress += i / num_parts / num_jobs
                    self.progress_update.emit(progress)

                    encode_start = max(start - self.options.pre_pad, 0)
                    encode_end = end-start + self.options.pre_pad + self.options.post_pad

                    part_out_path = tmp_path + F'/part{i}.mp3'

                    ffmpeg.call('-loglevel', 'panic',
                                '-ss', subtitles.secs_to_strtime(encode_start),
                                '-i', job.media_file,
                                '-t', subtitles.secs_to_strtime(encode_end),
                                '-q:a', '0', '-map', 'a',
                                part_out_path)
                    
                    part_list_f.write(F'file \'{part_out_path}\'\n')
                
                part_list_f.close()

                ffmpeg.call('-loglevel', 'panic',
                            '-f', 'concat', '-safe', '0',
                            '-i', part_list_path,
                            '-c', 'copy',
                            '-y',
                            job.output_file)

                if os.path.isfile(job.output_file) and job.output_file.endswith('.mp3'):
                    mp3file = eyed3.load(job.output_file)
                    tag = mp3file.tag
                    if self.metadata.album:
                        tag.album = self.metadata.album
                    if album_art_data is not None:
                        tag.images.set(3, album_art_data, album_art_mime)
                    tag.title = os.path.basename(job.output_file).replace('.mp3', '')
                    tag.track_num = job_idx + 1
                    tag.save()



class ConvertWindow(QDialog):

    def __init__(self, jobs, options, metadata, parent=None):
        super(ConvertWindow, self).__init__(parent)
        
        self.setWindowTitle('Converting...')
        self.setMinimumWidth(300)

        self.lyt = QVBoxLayout(self)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(10000)
        self.lyt.addWidget(self.progress_bar)

        self.thread = ConverterThread(jobs, options, metadata, self)
        self.thread.progress_update.connect(self.on_progress_update)
        self.thread.finished.connect(self.on_thread_done)
        self.thread.start()

    def on_thread_done(self):
        self.progress_bar.setValue(10000)
        self.close()

    def on_progress_update(self, progress):
        self.progress_bar.setValue(int(10000 * progress))

    def closeEvent(self, evt):
        if self.thread.isFinished():
            evt.accept()
        else:
            evt.ignore()
            self.ask_cancel()

    def ask_cancel(self):
        r = QMessageBox.warning(self, '', 'Do you really want to cancel the current conversions?', QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            self.thread.terminate()
