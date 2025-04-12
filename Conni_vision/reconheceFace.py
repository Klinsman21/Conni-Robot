import cv2
import numpy as np
import os

# Carregar modelo treinado
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')

# Nomes das pessoas (atualize conforme seus IDs de treinamento)
names = {
    0: "Desconhecido",
    1: "Joao",
    2: "Maria"
    # Adicione mais conforme necessário
}

# Carregar classificador de faces
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


def recognize_faces(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

    results = []
    for (x, y, w, h) in faces:
        id_, confidence = recognizer.predict(gray[y:y + h, x:x + w])

        if confidence < 70:  # Quanto menor, mais confiante
            name = names.get(id_, "Desconhecido")
        else:
            name = "Desconhecido"

        results.append({
            'bbox': (x, y, w, h),
            'name': name,
            'confidence': confidence
        })

    return results


def main():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # frame = cv2.flip(frame, 1)  # Espelhar a imagem
        faces = recognize_faces(frame)

        for face in faces:
            x, y, w, h = face['bbox']

            # Desenhar retângulo
            color = (0, 255, 0) if face['name'] != "Desconhecido" else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

            # Mostrar nome e confiança
            label = f"{face['name']} ({face['confidence']:.1f})"
            cv2.putText(frame, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow('Reconhecimento Facial', frame)

        if cv2.waitKey(1) == 27:  # ESC para sair
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    if not os.path.exists('trainer/trainer.yml'):
        print("Erro: Modelo não treinado. Execute primeiro train_face_recognition.py")
    else:
        main()