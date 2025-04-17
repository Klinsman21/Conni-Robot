import os
import wave
import json
from vosk import Model, KaldiRecognizer

# Caminho para o modelo
model_path = "vosk-model"

# Caminho para o arquivo de áudio
audio_file_path = "banheiro.wav"

# Carregar o modelo
model = Model(model_path)

# Abrir o arquivo de áudio (.wav)
wf = wave.open(audio_file_path, "rb")

# Verificar se o arquivo de áudio tem a taxa de amostragem correta (16 kHz)
if wf.getsampwidth() != 2 or wf.getframerate() != 16000:
    print("O arquivo de áudio precisa ser 16 kHz e estéreo de 16 bits.")
    exit(1)

# Inicializar o reconhecedor de fala
recognizer = KaldiRecognizer(model, wf.getframerate())

# Inicializar a transcrição
transcription = ""

# Processar o áudio em blocos
while True:
    data = wf.readframes(12000)
    if len(data) == 0:
        break
    recognizer.AcceptWaveform(data)
    temp = json.loads(recognizer.PartialResult())["partial"]
    if transcription != temp:
        transcription += temp

# Mostrar a transcrição final
print("Transcrição completa:")
print(transcription)
