#!/usr/bin/env python

import sys
import os
import re

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, pyqtSignal

import subtitles
import converter
import ffmpeg


def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)


class ClickableLable_Widget(QLabel):

    clicked = pyqtSignal()

    def __init__(self, text=''):
        super(ClickableLable_Widget, self).__init__(text)

    def mousePressEvent(self, evt):
        self.clicked.emit()


class HLine_Widget(QFrame):

    def __init__(self):
        super(HLine_Widget, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class FileSelector_Widget(QWidget):

    def __init__(self, title, is_save=False, filter='All Files (*.*)', select_txt='...', parent=None):
        super(FileSelector_Widget, self).__init__(parent)

        self.title = title
        self.is_save = is_save
        self.filter = filter

        self.lyt = QGridLayout(self)
        self.lyt.setContentsMargins(0, 0, 0, 0)
        
        self.lyt.addWidget(QLabel(title), 0, 0, 1, 2)

        self.button = QPushButton(select_txt)
        self.lyt.addWidget(self.button, 1, 0, 1, 1)

        self.line_edit = QLineEdit()
        self.lyt.addWidget(self.line_edit, 1, 1, 1, 1)

        self.button.clicked.connect(self.on_button)

    def on_button(self):
        if not self.is_save:
            new_path = QFileDialog.getOpenFileName(self, self.title, self.path(), self.filter)
        else:
            new_path = QFileDialog.getSaveFileName(self, self.title, self.path(), self.filter)
        if new_path[0]:
            self.line_edit.setText(new_path[0])

    def path(self):
        return self.line_edit.text()


class ExportCheck_Dialog(QDialog):

    def __init__(self, media_files, subtitle_files, output_files, parent=None):
        super(ExportCheck_Dialog, self).__init__(parent)

        self.setWindowTitle('Confirm Conversions')

        self.lyt = QVBoxLayout(self)

        self.lyt.addWidget(QLabel('Convert the following?'))

        self.table = QTableWidget()
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Media File', 'Subtitle File', 'Output File'])
        self.table.verticalHeader().setVisible(False)

        for (i, (media_file, subtitle_file, output_file)) in enumerate(zip(media_files, subtitle_files, output_files)):
            self.table.insertRow(self.table.rowCount())
            self.table.setItem(i, 0, QTableWidgetItem(media_file))
            self.table.setItem(i, 1, QTableWidgetItem(subtitle_file))
            self.table.setItem(i, 2, QTableWidgetItem(output_file))

        for i in range(self.table.columnCount()):
            self.table.resizeColumnToContents(i)

        self.lyt.addWidget(self.table)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok
                             | QDialogButtonBox.Cancel)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.lyt.addWidget(self.button_box)



class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle('Immersion Audio Tool')
        self.setMinimumWidth(600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.lyt = QVBoxLayout(self.central_widget)

        self.fs_media = FileSelector_Widget('Media File')
        self.lyt.addWidget(self.fs_media)

        self.fs_subtitle = FileSelector_Widget('Subtitle File', filter='Subtitle Files (*.srt *.ass)')
        self.lyt.addWidget(self.fs_subtitle)

        self.lyt.addWidget(HLine_Widget())

        self.condense_lyt = QGridLayout()
        self.condense_lyt.setContentsMargins(0, 0, 0, 0)

        self.condense_lyt_container = QHBoxLayout()
        self.condense_lyt_container.addLayout(self.condense_lyt)
        self.condense_lyt_container.addStretch()

        self.lyt.addLayout(self.condense_lyt_container)

        self.condense_lyt.addWidget(QLabel('Join Maximum:'), 0, 0)
        self.condense_join_max = QDoubleSpinBox()
        self.condense_join_max.setRange(0.0, 99.99)
        self.condense_join_max.setValue(2.0)
        self.condense_lyt.addWidget(self.condense_join_max, 0, 1)
        self.condense_lyt.addWidget(QLabel('seconds'), 0, 2)

        self.condense_lyt.addWidget(QLabel('Pre Padding:'), 1, 0)
        self.condense_pre_pad = QDoubleSpinBox()
        self.condense_pre_pad.setRange(-99.99, 99.99)
        self.condense_lyt.addWidget(self.condense_pre_pad, 1, 1)
        self.condense_lyt.addWidget(QLabel('seconds'), 1, 2)

        self.condense_lyt.addWidget(QLabel('Post Padding:'), 2, 0)
        self.condense_post_pad = QDoubleSpinBox()
        self.condense_post_pad.setRange(-99.99, 99.99)
        self.condense_lyt.addWidget(self.condense_post_pad, 2, 1)
        self.condense_lyt.addWidget(QLabel('seconds'), 2, 2)

        self.lyt.addWidget(HLine_Widget())

        self.metadata_lyt = QGridLayout()
        self.metadata_lyt.setContentsMargins(0, 0, 0, 0)

        self.metadata_lyt.addWidget(QLabel('Album Name:'), 0, 0)
        self.metadata_album = QLineEdit()
        self.metadata_lyt.addWidget(self.metadata_album, 0, 1)

        self.metadata_lyt.addWidget(QLabel('Album Art:'), 1, 0)

        self.metadata_album_art = ClickableLable_Widget('<None - Click to change>')
        self.metadata_album_art.setMaximumHeight(180)
        self.metadata_album_art.clicked.connect(self.on_album_art)
        self.album_art_path = None
        self.metadata_lyt.addWidget(self.metadata_album_art, 1, 1)

        self.lyt.addLayout(self.metadata_lyt)

        self.lyt.addWidget(HLine_Widget())

        self.fs_output = FileSelector_Widget('Output File', is_save=True, filter='MP3 (*.mp3)')
        self.lyt.addWidget(self.fs_output)

        self.lyt.addWidget(HLine_Widget())

        self.convert_btn = QPushButton('Convert')
        self.convert_btn.clicked.connect(self.on_convert)
        self.lyt.addWidget(self.convert_btn)

        self.lyt.addStretch()


    def on_convert(self):
        media_path = self.fs_media.path()
        subtitle_path = self.fs_subtitle.path()
        output_path = self.fs_output.path()

        media_files = natural_sort(self.files_from_path(media_path))

        if len(media_files) < 1:
            QMessageBox.warning(self, self.windowTitle(), 'No media input files found')
            return


        subtitle_files = []
        if subtitle_path.strip() == '':
            for media_file in media_files:
                subtitle_file = subtitles.find_sub_for_path(media_file)
                if subtitle_file is None:
                    QMessageBox.warning(self, self.windowTitle(), 'No subtitle file was found for\n\n' + media_file)
                    return
                subtitle_files.append(subtitle_file)
        else:
            subtitle_files = natural_sort(self.files_from_path(subtitle_path))

        output_files = []
        output_num_asterisk = output_path.count('*')
        if output_num_asterisk > 1:
            QMessageBox.warning(self, self.windowTitle(), 'The output path is invalid')
            return
        elif output_num_asterisk == 1:
            if len(media_files) > 1:
                start_cut = media_path.index('*')
                end_cut = len(media_path) - 1 - start_cut
                for media_file in media_files:
                    filter_fill = media_file[start_cut:-end_cut]
                    output_file = output_path.replace('*', filter_fill)
                    output_files.append(output_file)
        else:
            output_files = [output_path]

        if len(media_files) != len(subtitle_files):
            QMessageBox.warning(self, self.windowTitle(), 'Matching media files with subtitle files failed.')
            return

        if len(media_files) != len(output_files):
            QMessageBox.warning(self, self.windowTitle(), 'Matching media files with output files failed.')
            return

        r = ExportCheck_Dialog(media_files, subtitle_files, output_files, self).exec_()

        if r != ExportCheck_Dialog.Accepted:
            return

        jobs = [converter.Job(*t) for t in zip(media_files, subtitle_files, output_files)]

        options = converter.Options(
            self.condense_join_max.value(),
            self.condense_pre_pad.value(),
            self.condense_post_pad.value()
        )

        metadata = converter.Metadata(
            self.metadata_album.text().rstrip(),
            self.album_art_path
        )

        conv = converter.ConvertWindow(jobs, options, metadata, self)
        conv.exec_()

    def on_album_art(self):
        r = QFileDialog.getOpenFileName(self, 'Select Album Art', '', 'Image files (*.png *.jpg *.jpeg)')
        if not r[0]:
            self.album_art_path = None
            self.metadata_album_art.setText('<None - Click to change>')
            return

        self.album_art_path = r[0]
        self.metadata_album_art.setPixmap(QPixmap(self.album_art_path).scaledToHeight(180))



    def on_finished(self):
        QMessageBox.warning(self, self.windowTitle(), 'Finished!')


    @staticmethod
    def files_from_path(path):
        
        num_asterisk = path.count('*')

        if num_asterisk >= 2:
            return []
        if num_asterisk == 0:
            if os.path.isfile(path):
                return [path]
            else:
                return []

        dir_path = os.path.dirname(path)
        file_filter = os.path.basename(path)

        # Filter must be inside target dir
        if dir_path.find('*') >= 0:
            return []

        parts = file_filter.split('*')

        files = []

        for file_name in os.listdir(dir_path):
            file_path = dir_path + '/' + file_name
            if os.path.isfile(file_path):
                if file_name.startswith(parts[0]) and file_name.endswith(parts[1]):
                    files.append(file_path)

        return files



def main(argv):
    app = QApplication(argv)
    app.setOrganizationName("RicBent")
    app.setOrganizationDomain("http://bent.smbnext.net/")
    app.setApplicationName('ImmersionAudioTool')

    if not ffmpeg.init():
        return 0

    window = MainWindow()
    window.show()

    return app.exec_()


if __name__ == '__main__':
    ret = main(sys.argv)
    sys.exit(ret)
