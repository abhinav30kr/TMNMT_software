import sys
import sqlite3
from PySide6.QtCore import Qt, QUrl, QThreadPool, QRunnable, QObject, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QFileDialog, QComboBox, QSpinBox, QDoubleSpinBox, QWidget, QListWidget
from PySide6.QtGui import QIcon
from PySide6.QtMultimedia import QMediaPlayer
from scipy import signal 
import scipy.io.wavfile as wavfile

def design_notch_filter(frequency, quality_factor, sampling_rate):
    fs = sampling_rate  # Sampling rate
    f0 = frequency  # Notch frequency
    Q = quality_factor  # Quality factor

    # Design the IIR Notch filter
    b, a = signal.iirnotch(f0, Q, fs)

    return b, a

class MusicProcessingSignals(QObject):
    result = Signal(str)

class MusicProcessingRunnable(QRunnable):
    def __init__(self, file, selected_option, frequency, attenuation, parameter):
        super().__init__()
        self.file = file
        self.selected_option = selected_option
        self.frequency = frequency
        self.attenuation = attenuation
        self.parameter = parameter
        self.signals = MusicProcessingSignals()

    def run(self):
        if self.selected_option == "Notched Music Therapy":
            # Read the music file
            sampling_rate, audio_data = wavfile.read(self.file)
            # Calculate the filter coefficients for this file
            b, a = design_notch_filter(self.frequency, self.attenuation, sampling_rate)

            # Apply the Notch filter to the audio data
            filtered_audio = signal.lfilter(b, a, audio_data)

            # Save the filtered audio to a new file with a unique name
            file_name = self.file.split("/")[-1]  # Extract the file name from the full path
            output_file = file_name.replace(".wav", "_filtered.wav")
            wavfile.write(output_file, sampling_rate, filtered_audio.astype("int16"))
            self.signals.result.emit(output_file)

        elif self.selected_option == "Tinnitus Retraining Therapy":
            # Read the music file
            sampling_rate, audio_data = wavfile.read(self.file)
            # Process the file with Tinnitus Retraining Therapy here
            # ...

            # Save the processed audio to a new file with a unique name
            file_name = self.file.split("/")[-1]  # Extract the file name from the full path
            output_file = file_name.replace(".wav", "_processed.wav")
            wavfile.write(output_file, sampling_rate, audio_data)

            self.signals.result.emit(output_file)

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Music Processing")

        self.central_widget = QWidget(self)

        self.label = QLabel("Music Processing")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.select_button = QPushButton("Select Music Files")
        self.select_button.clicked.connect(self.select_music_files)

        self.process_button = QPushButton("Process Music Files")
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.process_music_files)

        self.options_combobox = QComboBox()
        self.options_combobox.addItem("Notched Music Therapy")
        self.options_combobox.addItem("Tinnitus Retraining Therapy")
        self.options_combobox.setEnabled(False)
        self.options_combobox.currentTextChanged.connect(self.on_option_selected)

        self.notch_frequency_spinbox = QSpinBox()
        self.notch_frequency_spinbox.setPrefix("Notch Frequency: ")
        self.notch_frequency_spinbox.setSuffix(" Hz")
        self.notch_frequency_spinbox.setMinimum(250)
        self.notch_frequency_spinbox.setMaximum(20000)
        self.notch_frequency_spinbox.setEnabled(False)

        self.attenuation_spinbox = QDoubleSpinBox()
        self.attenuation_spinbox.setPrefix("Attenuation Level: ")
        self.attenuation_spinbox.setSuffix(" dB")
        self.attenuation_spinbox.setEnabled(False)

        self.tinnitus_frequency_spinbox = QSpinBox()
        self.tinnitus_frequency_spinbox.setPrefix("Tinnitus Frequency: ")
        self.tinnitus_frequency_spinbox.setSuffix(" Hz")
        self.tinnitus_frequency_spinbox.setMinimum(250)
        self.tinnitus_frequency_spinbox.setMaximum(8000)
        self.tinnitus_frequency_spinbox.setEnabled(False)

        self.sound_files_list = QListWidget()

        self.media_player = QMediaPlayer(self)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.select_button)

        option_layout = QVBoxLayout()
        option_layout.addWidget(self.options_combobox)
        option_layout.addWidget(self.notch_frequency_spinbox)
        option_layout.addWidget(self.attenuation_spinbox)
        option_layout.addWidget(self.tinnitus_frequency_spinbox)

        layout.addLayout(option_layout)
        layout.addWidget(self.process_button)
        layout.addWidget(self.sound_files_list)

        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

        # Connect to the database
        self.conn = sqlite3.connect("output.db")
        self.cursor = self.conn.cursor()

        # Create table if not exists
        self.cursor.execute("CREATE TABLE IF NOT EXISTS processed_files (file_path TEXT, therapy_type TEXT, notch_frequency REAL, parameter REAL, attenuation REAL)")
        self.conn.commit()

        # Initialize media player
        self.media_player = QMediaPlayer(self)

    def select_music_files(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Music Files (*.mp3 *.wav *.ogg)")

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.selected_files = selected_files
                self.process_button.setEnabled(True)
                self.options_combobox.setEnabled(True)
                self.notch_frequency_spinbox.setEnabled(True)
                self.attenuation_spinbox.setEnabled(True)
                self.tinnitus_frequency_spinbox.setEnabled(True)

                # Add selected files to the sound files list
                self.sound_files_list.clear()
                self.sound_files_list.addItems(selected_files)

    def on_option_selected(self, selected_option):
        if selected_option == "Notched Music Therapy":
            self.notch_frequency_spinbox.setVisible(True)
            self.attenuation_spinbox.setVisible(True)
            self.tinnitus_frequency_spinbox.setVisible(False)
        elif selected_option == "Tinnitus Retraining Therapy":
            self.notch_frequency_spinbox.setVisible(False)
            self.attenuation_spinbox.setVisible(False)
            self.tinnitus_frequency_spinbox.setVisible(True)

    def process_music_files(self):
        selected_files = self.selected_files
        selected_option = self.options_combobox.currentText()

        # Create a new thread pool
        thread_pool = QThreadPool.globalInstance()

        for file in selected_files:
            if selected_option == "Notched Music Therapy":
                attenuation = self.attenuation_spinbox.value()
                notch_frequency = self.notch_frequency_spinbox.value()

                # Create a new runnable for each file with the correct filter parameters
                runnable = MusicProcessingRunnable(file, selected_option, notch_frequency, attenuation, None)
                runnable.signals.result.connect(self.on_processing_complete)

                # Start processing the file in a separate thread
                thread_pool.start(runnable)

            elif selected_option == "Tinnitus Retraining Therapy":
                tinnitus_frequency = self.tinnitus_frequency_spinbox.value()

                # Create a new runnable for each file with the correct parameter
                runnable = MusicProcessingRunnable(file, selected_option, None, None, tinnitus_frequency)
                runnable.signals.result.connect(self.on_processing_complete)

                # Start processing the file in a separate thread
                thread_pool.start(runnable)

    def on_processing_complete(self, output_file):
        if output_file:
            # Update the sound files list
            self.sound_files_list.addItem(output_file)

            # Play the processed music file
            self.play_music(output_file)

    def play_music(self, file):
        # Create a media content from the file
        media_content = QUrl.fromLocalFile(file)

        # Set the media content to the media player
        self.media_player.setMedia(media_content)

        # Play the music
        self.media_player.play()

if __name__ == "__main__":
    app = QApplication([])
    app.setWindowIcon(QIcon("sample.png"))
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec())
