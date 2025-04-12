import cv2
import numpy as np
import os

# Criar diretórios se não existirem
if not os.path.exists('dataset'):
    os.makedirs('dataset')
if not os.path.exists('trainer'):
    os.makedirs('trainer')

# Inicializar detector de faces
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()


def capture_training_samples(person_id, num_samples=80):
    """Captura amostras para treinamento"""
    cap = cv2.VideoCapture(0)
    count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            count += 1
            # Salvar a imagem capturada
            cv2.imwrite(f"dataset/User.{person_id}.{count}.jpg", gray[y:y + h, x:x + w])

        cv2.putText(frame, f"Amostras coletadas: {count}/{num_samples}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow('Coletando Amostras para Treinamento', frame)

        if count >= num_samples or cv2.waitKey(100) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


def train_model():
    """Treina o modelo com as imagens coletadas"""
    faces = []
    ids = []

    for filename in os.listdir('dataset'):
        if filename.startswith('User.'):
            id = int(filename.split('.')[1])
            path = os.path.join('dataset', filename)
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

            if img is not None:
                faces.append(img)
                ids.append(id)

    if len(faces) == 0:
        print("Erro: Nenhuma imagem encontrada no diretório 'dataset'")
        return

    recognizer.train(faces, np.array(ids))
    recognizer.write('trainer/trainer.yml')
    print(f"Modelo treinado com {len(faces)} imagens de {len(set(ids))} pessoas")


if __name__ == "__main__":
        person_id = input("Digite o ID numérico da pessoa: ")
        capture_training_samples(int(person_id))
        train_model()