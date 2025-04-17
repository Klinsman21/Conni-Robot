from pydub import AudioSegment

# Caminho do arquivo MP3
mp3_file = "banheiro.mp3"
# Caminho onde salvar o arquivo WAV
wav_file = "banheiro.wav"

# Carregar o arquivo MP3
audio = AudioSegment.from_mp3(mp3_file)

# Salvar como WAV com taxa de amostragem de 16kHz
audio = audio.set_frame_rate(16000)  # Ajustando para 16 kHz
audio = audio.set_channels(1)  # Mono
audio.export(wav_file, format="wav")

import wave

with wave.open("banheiro.wav", "rb") as wf:
    print(f"Taxa de amostragem: {wf.getframerate()}")
    print(f"Canal: {wf.getnchannels()}")
    print(f"Profundidade de amostragem: {wf.getsampwidth()}")
