import cv2
import numpy as np
from pyzbar.pyzbar import decode

# Carregar modelos
net = cv2.dnn.readNetFromCaffe("deploy.prototxt", "mobilenet_iter_73000.caffemodel")

# Inicializar detector facial YuNet (baixe o modelo em https://github.com/opencv/opencv_zoo/tree/master/models/face_detection_yunet)
face_detector = cv2.FaceDetectorYN.create(
    "face_detection_yunet_2023mar.onnx",  # Caminho para o modelo
    "",
    (320, 320),  # Tamanho de entrada do modelo
    0.8,  # Confiança mínima
    0.3,  # NMS threshold
    5000  # Top K
)

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer.yml')

# Nomes das pessoas (atualize conforme seus IDs de treinamento)
names = {
    0: "Desconhecido",
    1: "Joao",
    2: "Maria"
    # Adicione mais conforme necessário
}

TAMANHO_REAL_CM = 10.0  # Tamanho real do ArUco (10 cm)
FOCAL_LENGTH = 600  # Ajuste conforme a calibração da câmera
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_16H5)
aruco_params = cv2.aruco.DetectorParameters()

# Inicializar câmera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Configurações
TRACKER_TYPE = 'KCF'
REDETECTION_INTERVAL = 15
MIN_FACE_SIZE = 100
FACE_CONFIDENCE = 0.7  # Confiança mínima para detecção facial

# Variáveis de estado
tracking = False
tracker = None
mode = "body"
frame_count = 0


def create_tracker():
    if TRACKER_TYPE == 'CSRT':
        return cv2.TrackerCSRT_create()
    elif TRACKER_TYPE == 'KCF':
        return cv2.TrackerKCF_create()
    else:
        return cv2.TrackerMOSSE_create()


def detect_aruco(frame):
    corners, ids, _ = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=aruco_params)

    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        for i in range(len(ids)):
            center = np.mean(corners[i][0], axis=0).astype(int)
            # Calcular a largura do ArUco na imagem
            largura_pixels = np.linalg.norm(corners[i][0][0] - corners[i][0][1])

            # Estimar a distância
            distancia = (TAMANHO_REAL_CM * FOCAL_LENGTH) / largura_pixels

            # Mostrar a distância
            cv2.putText(frame, f"{distancia:.2f} cm", (center[0] - 20, center[1] + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    return ids is not None


def detect_body(frame):
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    best_conf = 0
    best_box = None

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        idx = int(detections[0, 0, i, 1])

        if confidence > 0.5 and idx == 15:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            box_w = endX - startX
            box_h = endY - startY

            if confidence > best_conf and box_h / box_w > 1.5:
                best_conf = confidence
                best_box = (startX, startY, box_w, box_h)

    return best_box


# def detect_face(frame):
#     # Redimensionar para o tamanho esperado pelo YuNet (320x320)
#     resized = cv2.resize(frame, (320, 320))
#
#     # Configurar o tamanho de entrada do detector
#     face_detector.setInputSize((320, 320))
#
#     # Detectar faces
#     _, faces = face_detector.detect(resized)
#
#     if faces is not None:
#         for face in faces:
#             confidence = face[-1]
#             if confidence > FACE_CONFIDENCE:
#                 # Converter coordenadas de volta para o tamanho original
#                 x = int(face[0] * frame.shape[1] / 320)
#                 y = int(face[1] * frame.shape[0] / 320)
#                 w = int(face[2] * frame.shape[1] / 320)
#                 h = int(face[3] * frame.shape[0] / 320)
#
#                 if w > MIN_FACE_SIZE:
#                     return (x, y, w, h)
#
#     return None

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


while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    # frame = cv2.flip(frame, 1)

    if frame_count % 5 == 0 or not tracking:
        aruco_detected = detect_aruco(frame)

    # --- Detecção/Rastreamento ---
    if not tracking or frame_count % REDETECTION_INTERVAL == 0:
        face_box = None#detect_face(frame)

        if face_box is not None:
            (x, y, w, h) = face_box
            mode = "face"
            tracker = create_tracker()
            tracker.init(frame, (x, y, w, h))
            tracking = True
        else:
            body_box = detect_body(frame)
            if body_box is not None:
                (x, y, w, h) = body_box
                mode = "body"
                tracker = create_tracker()
                tracker.init(frame, (x, y, w, h))
                tracking = True
            else:
                tracking = False

    elif tracking:
        success, box = tracker.update(frame)
        if success:
            (x, y, w, h) = [int(v) for v in box]

            # Atualizar modo se necessário
            if mode == "face" and w < MIN_FACE_SIZE:
                body_box = detect_body(frame)
                if body_box is not None:
                    (x, y, w, h) = body_box
                    mode = "body"
                    tracker = create_tracker()
                    tracker.init(frame, (x, y, w, h))
            elif mode == "body" and w * h > 100000:
                face_box = detect_face(frame)
                if face_box is not None:
                    (x, y, w, h) = face_box
                    mode = "face"
                    tracker = create_tracker()
                    tracker.init(frame, (x, y, w, h))

            # Desenhar e mostrar informações
            color = (0, 255, 0) if mode == "body" else (255, 0, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

            label = "ROSTO" if mode == "face" else "CORPO"
            cv2.putText(frame, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.putText(frame, f"{w}x{h}", (x, y + h + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        else:
            tracking = False

    # Status e FPS
    fps = cap.get(cv2.CAP_PROP_FPS)
    status = f"Modo: {mode.upper()} | Tracking: {'ON' if tracking else 'OFF'} | FPS: {int(fps)}"
    cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("Rastreamento + ArUco", frame)

    key = cv2.waitKey(1)
    if key == 27:
        break
    elif key == ord('t'):
        TRACKER_TYPE = 'KCF' if TRACKER_TYPE == 'CSRT' else 'CSRT'
        tracking = False

cap.release()
cv2.destroyAllWindows()