# from vosk import Model, KaldiRecognizer
# import pyaudio
#
# model = Model("vosk-full")  # Baixe modelos em: https://alphacephei.com/vosk/models
# recognizer = KaldiRecognizer(model, 16000)
#
# mic = pyaudio.PyAudio()
# stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
#
# print("Fale algo...")
# while True:
#     data = stream.read(4096)
#     if recognizer.AcceptWaveform(data):
#         result = recognizer.Result()
#         print("Texto: " + result)
# import os
# import sys
#
# import whisper
# os.environ["PATH"] += os.pathsep + r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin"
# model = whisper.load_model("turbo")  # Pode usar tiny, base, small, medium, large
# result = model.transcribe("banheiro.mp3", language="pt")
# print(result["text"])



import pvporcupine
import pyaudio
import struct
import wave
import whisper
import os
import numpy as np
from datetime import datetime
os.environ["PATH"] += os.pathsep + r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin"
# Configurações do Porcupine
ACCESS_KEY = "Cs8x38L7PEzKO5G1fA0xN8/gycHKT3UvSJZJ+WwIf7hEh1c7/TBxBw=="
KEYWORD_PATH = "conni.ppn"
MODEL_PATH = "porcupine_pt.pv"

# Configurações de áudio
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
SILENCE_THRESHOLD = 500  # Ajuste conforme necessário para sensibilidade ao silêncio
SILENCE_DURATION = 1.2  # Segundos de silêncio para encerrar
MAX_RECORD_SECONDS = 5.0  # Tempo máximo de gravação

# Inicializa o Whisper (use 'tiny' ou 'base' para Raspberry Pi)
model = whisper.load_model("tiny")

# Inicializa o Porcupine
porcupine = pvporcupine.create(
    access_key=ACCESS_KEY,
    keyword_paths=[KEYWORD_PATH],
    model_path=MODEL_PATH
)

# Configura o microfone
audio = pyaudio.PyAudio()
stream = audio.open(
    rate=porcupine.sample_rate,
    channels=CHANNELS,
    format=FORMAT,
    input=True,
    frames_per_buffer=porcupine.frame_length
)

print("Aguardando a palavra-chave 'Conni'...")


def gravar_audio_com_deteccao():
    frames = []
    silent_frames = 0
    silence_threshold_frames = int(SILENCE_DURATION * RATE / porcupine.frame_length)
    max_frames = int(MAX_RECORD_SECONDS * RATE / porcupine.frame_length)

    print("Gravando... Diga seu comando.")

    for i in range(max_frames):
        data = stream.read(porcupine.frame_length, exception_on_overflow=False)
        frames.append(data)

        # Converte para numpy array para detectar silêncio
        audio_data = np.frombuffer(data, dtype=np.int16)
        if np.abs(audio_data).mean() < SILENCE_THRESHOLD:
            silent_frames += 1
            if silent_frames > silence_threshold_frames:
                print("Silêncio detectado, encerrando gravação.")
                break
        else:
            silent_frames = 0

    # Salva o arquivo de áudio
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_file = f"comando_{timestamp}.wav"

    wf = wave.open(audio_file, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    return audio_file


try:
    while True:
        data = stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * porcupine.frame_length, data)
        result = porcupine.process(pcm)

        if result >= 0:
            print("\nPalavra-chave detectada!")
            audio_file = gravar_audio_com_deteccao()

            # Transcreve o áudio com Whisper
            result = model.transcribe(audio_file, language="pt")
            texto = result["text"].strip()

            print(f"Comando reconhecido: {texto}")

            # Aqui você pode adicionar a lógica para processar o comando
            # Exemplo: if "ligar luz" in texto.lower():
            #             ligar_luz()

            # Remove o arquivo de áudio após processamento (opcional)
            os.remove(audio_file)

            print("\nAguardando próximo comando...")

except KeyboardInterrupt:
    print("\nEncerrando...")
finally:
    stream.close()
    audio.terminate()