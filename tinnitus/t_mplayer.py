import sys
import sqlite3
import scipy
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QFileDialog, QComboBox, QFormLayout, QSpinBox, QDoubleSpinBox, QWidget, QLineEdit, QListWidget
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

        self.sampling_frequency_spinbox = QSpinBox()
        self.sampling_frequency_spinbox.setPrefix("Sampling Frequency: ")
        self.sampling_frequency_spinbox.setSuffix(" Hz")
        self.sampling_frequency_spinbox.setMinimum(250)
        self.sampling_frequency_spinbox.setMaximum(8000)
        self.sampling_frequency_spinbox.setEnabled(False)

        self.notch_frequency_spinbox = QSpinBox()
        self.notch_frequency_spinbox.setPrefix("Notch Frequency: ")
        self.notch_frequency_spinbox.setSuffix(" Hz")
        self.notch_frequency_spinbox.setMinimum(250)
        self.notch_frequency_spinbox.setMaximum(8000)
        self.notch_frequency_spinbox.setEnabled(False)

        self.attenuation_spinbox = QDoubleSpinBox()
        self.attenuation_spinbox.setPrefix("Attenuation Level: ")
        self.attenuation_spinbox.setSuffix(" dB")
        self.attenuation_spinbox.setEnabled(False)

        self.parameter_label = QLabel("Parameter of Narrow Band Noise:")
        self.parameter_label.setVisible(False)

        self.parameter_spinbox = QDoubleSpinBox()
        self.parameter_spinbox.setVisible(False)

        self.sound_files_list = QListWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.select_button)

        option_layout = QVBoxLayout()
        option_layout.addWidget(self.options_combobox)
        option_layout.addWidget(self.sampling_frequency_spinbox)
        option_layout.addWidget(self.notch_frequency_spinbox)
        option_layout.addWidget(self.attenuation_spinbox)

        layout.addLayout(option_layout)
        layout.addWidget(self.parameter_label)
        layout.addWidget(self.parameter_spinbox)
        layout.addWidget(self.process_button)
        layout.addWidget(self.sound_files_list)

        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

        # Connect to the database
        self.conn = sqlite3.connect("output.db")
        self.cursor = self.conn.cursor()

        # Create table if not exists
        self.cursor.execute("CREATE TABLE IF NOT EXISTS processed_files (file_path TEXT, therapy_type TEXT, sampling_frequency REAL, notch_frequency REAL, parameter REAL, attenuation REAL)")
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
                self.sampling_frequency_spinbox.setEnabled(True)
                self.notch_frequency_spinbox.setEnabled(True)
                self.attenuation_spinbox.setEnabled(True)
                self.parameter_label.setVisible(False)
                self.parameter_spinbox.setVisible(False)
                self.parameter_spinbox.setValue(0.0)

                # Add selected files to the sound files list
                self.sound_files_list.clear()
                self.sound_files_list.addItems(selected_files)

    def on_option_selected(self, selected_option):
        if selected_option == "Notched Music Therapy":
            self.parameter_label.setVisible(False)
            self.parameter_spinbox.setVisible(False)
            self.sampling_frequency_spinbox.setVisible(True)
            self.notch_frequency_spinbox.setVisible(True)
            self.sampling_frequency_spinbox.setEnabled(True)
            self.notch_frequency_spinbox.setEnabled(True)
            self.attenuation_spinbox.setEnabled(True)
        elif selected_option == "Tinnitus Retraining Therapy":
            self.parameter_label.setVisible(True)
            self.parameter_spinbox.setVisible(True)
            self.sampling_frequency_spinbox.setVisible(False)
            self.notch_frequency_spinbox.setVisible(False)
            self.sampling_frequency_spinbox.setEnabled(False)
            self.notch_frequency_spinbox.setEnabled(False)
            self.attenuation_spinbox.setEnabled(False)

    def process_music_files(self):
        selected_files = self.selected_files
        selected_option = self.options_combobox.currentText()
        frequency = self.notch_frequency_spinbox.value()

        for file in selected_files:
            if selected_option == "Notched Music Therapy":
                attenuation = self.attenuation_spinbox.value()
                sampling_frequency = self.sampling_frequency_spinbox.value()
                notch_frequency = self.notch_frequency_spinbox.value()
                print("Processing music file with Notched Music Therapy:")
                print("File:", file)
                print("Sampling Frequency:", sampling_frequency, "Hz")
                print("Notch Frequency:", notch_frequency, "Hz")
                print("Attenuation Level:", attenuation, "dB")

                # Design the Notch filter
                b, a = design_notch_filter(frequency, attenuation, sampling_frequency)

                # Read the music file
                sampling_rate, audio_data = wavfile.read(file)

                # Apply the Notch filter to the audio data
                filtered_audio = signal.lfilter(b, a, audio_data)

                # Save the filtered audio to a new file
                output_file = file.replace(".wav", "_filtered.wav")
                wavfile.write(output_file, sampling_rate, filtered_audio)


                # Insert data into the database
                self.cursor.execute("INSERT INTO processed_files (file_path, therapy_type, sampling_frequency, notch_frequency, parameter, attenuation) VALUES (?, ?, ?, ?, ?, ?)",
                                    (file, selected_option, sampling_frequency, notch_frequency, None, attenuation))
                self.conn.commit()

                # Update the sound files list
                self.sound_files_list.addItem(output_file)

                # Play the original music file
                self.play_music(file)

                # Play the processed music file
                self.play_music(output_file)

            elif selected_option == "Tinnitus Retraining Therapy":
                parameter = self.parameter_spinbox.value()
                print("Processing music file with Tinnitus Retraining Therapy:")
                print("File:", file)
                print("Parameter of Narrow Band Noise:", parameter)

                # Insert data into the database
                self.cursor.execute("INSERT INTO processed_files (file_path, therapy_type, sampling_frequency, notch_frequency, parameter, attenuation) VALUES (?, ?, ?, ?, ?, ?)",
                                    (file, selected_option, None, None, parameter, None))
                self.conn.commit()

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

