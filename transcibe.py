import sys
import nemo.collections.asr as nemo_asr
import os
from pydub import AudioSegment
import datetime
import wave
import pyaudio
import speech_recognition as sr

from moviepy.editor import VideoFileClip




from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QListWidget
)
from PyQt6.QtCore import QObject, QThread, pyqtSignal
t=2
speech_recognizer = sr.Recognizer()
asr_model = nemo_asr.models.EncDecCTCModelBPE.restore_from(restore_path="stt_ru_conformer_ctc_large.nemo")
a=[]
# Step 1: Create a worker class
class Worker(QObject):
    global a
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    def run(self):
        """Long-running task."""
        for file  in a:
            print(str(file))
            filename, ext = os.path.splitext(file)
            current_file=file
            if (ext in ['.mp4','.mov']):
                clip = VideoFileClip(file)
                clip.audio.write_audiofile(f"{filename}.{'wav'}")
                current_file=f"{filename}.{'wav'}"
            elif (ext in [".mp3",".ogg"]):
                continue
                if (ext=='.mp3'):
                    sound=AudioSegment.from_mp3(current_file)
                    sound.export(f"{filename}.{'wav'}",format='wav')

                elif (ext=='.ogg'):
                    sound=AudioSegment.from_ogg(current_file)
                    sound.export(f"{filename}.{'wav'}",format='wav')
                current_file=f"{filename}.{'wav'}"
            if (current_file.split('.')[-1]!='wav'):
                continue
            if t == 1:
                print(f"Проверка файла {current_file}")

                try:
                    try:
                        with sr.AudioFile(current_file) as source:
                            audio_data = speech_recognizer.record(source)
                    except:
                        print(f"error_with_reading {current_file}")
                        ...
                    text = speech_recognizer.recognize_google(audio_data,language="ru",show_all=True)
                    print(*text)
                    self.finished.emit()
                except:
                    print('error')
                    ...
            elif t == 2:
                text=[""]
                try:
                    nc=1
                    print(current_file)
                    try:
                        f=wave.open(current_file,"rb")
                        nc=f.getnchannels()
                        f.close()
                    except:
                        ...
                    print(nc)
                    if (nc==1):
                        text = asr_model.transcribe(paths2audio_files=[current_file], batch_size=4, logprobs=False)
                    else:
                        text = asr_model.transcribe(paths2audio_files=[current_file],batch_size=4,logprobs=False,channel_selector="average")
                except:
                    print("error2")
                    ...
                print(text)
                new_file=open(current_file.split('.')[0]+'.txt','w+')
                new_file.write(text[0])
                new_file.close()
                self.finished.emit()
        a.clear()

class worker2(QObject):
    recording_finished = pyqtSignal()
    progress = pyqtSignal(str)
    def record_speech(self):
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024
        RECORD_SECONDS = 30
        WAVE_OUTPUT_FILENAME = "output" + str(datetime.datetime.now().time()) + ".wav"
        audio = pyaudio.PyAudio()
        # открытие потока для записи
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)

        win.stepLabel.setText("Запись...")

        frames = []
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
        win.stepLabel.setText("Запись завершена.")
        # остановка потока
        stream.stop_stream()
        stream.close()
        audio.terminate()
        # сохранение записанного звука в файл
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        self.recording_finished.emit()

class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.Counter = 0
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("File annotator")
        self.resize(300, 150)
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        # Create and connect widgets

        self.stepLabel = QLabel("Not started")
        self.stepLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.record_audio=QPushButton("Record some audio(30 seconds)!",self)
        self.record_audio.clicked.connect(self.recording_task)

        self.open_files = QPushButton("Open some files!", self)
        self.open_files.clicked.connect(self.getfile)

        self.directory = QPushButton("Open Directory!", self)
        self.directory.clicked.connect(self.open_dir_dialog)

        self.longRunningBtn = QPushButton("Transcribe!", self)
        self.longRunningBtn.clicked.connect(self.transcibingTask)
        self.file_list=QListWidget()
        # Set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.record_audio)
        layout.addWidget(self.open_files)
        layout.addWidget(self.directory)
        layout.addStretch()
        layout.addWidget(self.stepLabel)
        layout.addWidget(self.longRunningBtn)
        layout.addWidget(self.file_list)
        self.centralWidget.setLayout(layout)

        button_action = QAction("&Google Cloud API", self)
        button_action.setStatusTip("Change model to Google Cloud API")
        button_action.triggered.connect(self.change_to_sr)
        button_action.setCheckable(True)

        button_action2 = QAction("&NVIDIA NeMo conformer_ctc_large", self)
        button_action2.setStatusTip("Change model to NeMo conformer_ctc_large")
        button_action2.triggered.connect(self.change_to_nemo)
        button_action2.setCheckable(True)
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("&Настройки")
        self.file_submenu = self.file_menu.addMenu("&Изменить модель")
        self.file_submenu.addAction(button_action)
        self.file_submenu.addAction(button_action2)
    def change_to_sr(self):
        global t
        t=1
    def change_to_nemo(self):
        global t
        t=2
    def getfile(self):
        dialog = QFileDialog(self)
        dialog.setDirectory(r'C:')
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setViewMode(QFileDialog.ViewMode.List)
        if dialog.exec():
            filenames = dialog.selectedFiles()
            if filenames:
                self.file_list.addItems([str(Path(filename)) for filename in filenames])
                self.Counter+=len(filenames)
    def open_dir_dialog(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select a Directory")
        if dir_name:
            path = Path(dir_name)
            self.file_list.addItems([str(path)])
            self.Counter+=1
            for filename in os.listdir(dir_name):
                f=os.path.join(dir_name,filename)
                if os.path.isfile(f) and (filename.endswith('wav') or filename.endswith('mp4') or filename.endswith('mov')):
                    a.append(f)

    def reportProgress(self):
        self.stepLabel.setText(f"in progress: ")
    def recording_task(self):
        self.reportProgress()
        """Long-running task in 5 steps."""
        self.thread2 = QThread()
        # Step 3: Create a worker object
        self.Worker2 = worker2()
        # Step 4: Move worker to the thread
        self.Worker2.moveToThread(self.thread2)
        # Step 5: Connect signals and slots
        self.thread2.started.connect(self.Worker2.record_speech)
        self.Worker2.recording_finished.connect(self.thread2.quit)
        self.Worker2.recording_finished.connect(self.Worker2.deleteLater)
        self.thread2.finished.connect(self.thread2.deleteLater)
        self.Worker2.progress.connect(self.reportProgress)
        # Step 6: Start the thread
        self.thread2.start()

        # Final resets
        self.longRunningBtn.setEnabled(False)
        self.thread2.finished.connect(
            lambda: self.longRunningBtn.setEnabled(True)
        )
        self.thread2.finished.connect(
            lambda: self.stepLabel.setText("finished")
        )
    def transcibingTask(self):
        self.reportProgress()
        for i in range(self.Counter):
            orgfilename=self.file_list.item(i).text()
            a.append(orgfilename)
            print(orgfilename)
        self.file_list.clear()
        self.Counter=0
        """Long-running task in 5 steps."""
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = Worker()
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.reportProgress)
        # Step 6: Start the thread
        self.thread.start()

        # Final resets
        self.longRunningBtn.setEnabled(False)
        self.thread.finished.connect(
            lambda: self.longRunningBtn.setEnabled(True)
        )
        self.thread.finished.connect(
            lambda: self.stepLabel.setText("finished")
        )

app = QApplication(sys.argv)
win = Window()
win.show()
sys.exit(app.exec())