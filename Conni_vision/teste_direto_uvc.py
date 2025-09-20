"""
Teste Direto UVC + Face Tracking FM888
Lê frames da câmera UVC e exibe rastreamento facial baseado APENAS nos dados do sensor FM888
NÃO usa detecção de face do OpenCV - apenas dados do sensor via serial
"""

import cv2
import time
import threading
import queue
from fm import FM

# Configurações
CAMERA_INDEX = 0
SERIAL_PORT = "COM11"
BAUDRATE = 115200

# Variáveis globais para compartilhamento entre threads
face_data_queue = queue.Queue(maxsize=5)
current_face = None
sensor = None
running = True

def face_tracking_thread():
    """Thread para rastreamento facial independente"""
    global current_face, running
    
    try:
        print("🎯 Iniciando rastreamento facial...")
        
        while running:
            try:
                print("🔍 Chamando sensor.verify()...")
                result = sensor.verify_sync(timeout_s=10, show_face_tracking=False)
                
                # Processa dados de face se disponíveis
                face_data = result.get('face_data', [])
                if face_data:
                    print(f"✅ Verificação concluída: {len(face_data)} frames coletados")
                    
                    # Processa todos os frames de face
                    for face_info in face_data:
                        if not running:
                            break
                            
                        face_info['timestamp'] = time.time()
                        current_face = face_info
                        
                        # Adiciona à fila
                        try:
                            face_data_queue.put_nowait(face_info)
                        except queue.Full:
                            pass
                    
                    # Mostra estatísticas
                    faces_detectadas = [f for f in face_data if f['state'] > 0]
                    print(f"📊 Estatísticas: {len(faces_detectadas)}/{len(face_data)} frames com face detectada")
                    
                else:
                    print("👁️ Nenhuma face detectada durante a verificação")
                
                # Pequena pausa antes da próxima verificação
                if running:
                    print("⏳ Aguardando 1 segundo antes da próxima verificação...")
                    time.sleep(1.0)
                
            except Exception as e:
                print(f"⚠️ Erro na verificação: {e}")
                if running:
                    print("⏳ Aguardando 2 segundos antes de tentar novamente...")
                    time.sleep(2.0)
                
    except Exception as e:
        print(f"❌ Erro no rastreamento facial: {e}")

def main():
    global sensor, running
    
    print("🎯 Teste Direto UVC + Face Tracking FM888")
    print("📹 Stream independente do sensor")
    
    # Abre câmera
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"❌ Erro: Câmera {CAMERA_INDEX} não encontrada")
        return
    
    # Configura câmera para melhor performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduz buffer para menor latência
    
    # Desativa qualquer detecção automática de faces do OpenCV
    cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)  # Força conversão RGB
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)  # Desativa auto-exposição
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Desativa auto-foco
    
    # Conecta sensor
    try:
        sensor = FM(SERIAL_PORT, BAUDRATE)
        sensor.reset()
        sensor.set_face_box(True)
        print(f"✅ Sensor conectado na porta {SERIAL_PORT}")
    except Exception as e:
        print(f"❌ Erro ao conectar sensor: {e}")
        cap.release()
        return
    
    # Inicia thread de rastreamento facial
    tracking_thread = threading.Thread(target=face_tracking_thread, daemon=True)
    tracking_thread.start()
    print("🎯 Thread de rastreamento facial iniciada")
    
    print("📹 Streaming iniciado! Pressione 'q' para sair")
    
    frame_count = 0
    last_fps_time = time.time()
    fps = 0
    
    try:
        while True:
            # Lê frame da câmera (não bloqueia)
            ret, frame = cap.read()
            if not ret:
                print("❌ Erro ao capturar frame")
                break
            
            # Garante que o frame está limpo (sem detecção automática)
            # Cria uma cópia limpa do frame para evitar interferências
            clean_frame = frame.copy()
            
            frame_count += 1
            current_time = time.time()
            
            # Calcula FPS
            if current_time - last_fps_time >= 1.0:
                fps = frame_count / (current_time - last_fps_time)
                frame_count = 0
                last_fps_time = current_time
            
            # Processa dados de face do SENSOR FM888 (não OpenCV)
            if current_face and current_face['state'] > 0:  # Face detectada pelo sensor
                bbox = current_face['bbox']
                yaw, pitch, roll = current_face['yaw'], current_face['pitch'], current_face['roll']
                
                # Valida se os dados do sensor são válidos
                if (bbox and len(bbox) == 4 and 
                    bbox[0] >= 0 and bbox[1] >= 0 and 
                    bbox[2] > bbox[0] and bbox[3] > bbox[1]):
                    
                    # Converte coordenadas do sensor FM888 para câmera UVC
                    sensor_width, sensor_height = 640, 480  # Resolução do sensor FM888
                    cam_width, cam_height = clean_frame.shape[1], clean_frame.shape[0]
                    
                    left = int(bbox[0] * cam_width / sensor_width)
                    top = int(bbox[1] * cam_height / sensor_height)
                    right = int(bbox[2] * cam_width / sensor_width)
                    bottom = int(bbox[3] * cam_height / sensor_height)
                    
                    # Valida se as coordenadas estão dentro da imagem
                    if (0 <= left < cam_width and 0 <= top < cam_height and 
                        left < right <= cam_width and top < bottom <= cam_height):
                        
                        # Desenha APENAS o retângulo da face do sensor FM888
                        cv2.rectangle(clean_frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        
                        # Desenha informações da face do sensor
                        info_text = f"FM888: {right-left}x{bottom-top}"
                        cv2.putText(clean_frame, info_text, (left, top-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                        angles_text = f"Y:{yaw}° P:{pitch}° R:{roll}°"
                        cv2.putText(clean_frame, angles_text, (left, top+20), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                        
                        # Centro da face (dados do sensor)
                        center_x = (left + right) // 2
                        center_y = (top + bottom) // 2
                        cv2.circle(clean_frame, (center_x, center_y), 3, (0, 255, 0), -1)
                    else:
                        print(f"⚠️ Coordenadas inválidas: left={left}, top={top}, right={right}, bottom={bottom}")
                else:
                    print(f"⚠️ Dados do sensor inválidos: bbox={bbox}")
            
            # Desenha informações do sistema
            cv2.putText(clean_frame, f"FPS: {fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(clean_frame, f"Camera UVC: {CAMERA_INDEX}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(clean_frame, f"FM888: {SERIAL_PORT}", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Status da face (apenas dados do sensor FM888)
            if current_face and current_face['state'] > 0:
                cv2.putText(clean_frame, "FM888 Face: DETECTADA", (10, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(clean_frame, "FM888 Face: NENHUMA", (10, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Exibe a imagem com rastreamento (apenas dados do sensor FM888)
            cv2.imshow('FM888 UVC + Face Tracking (Sensor Only)', clean_frame)
            
            # Pressione 'q' para sair
            key = cv2.waitKey(1)
            if key != -1:
                try:
                    if chr(int(key) & 0xFF) == 'q':
                        break
                except:
                    pass
    
    except KeyboardInterrupt:
        print("\n⏹️ Interrompido pelo usuário")
    
    finally:
        # Para thread de rastreamento
        running = False
        
        # Limpa recursos
        cap.release()
        if sensor:
            sensor.close()
        cv2.destroyAllWindows()
        print("✅ Fim do teste")

if __name__ == "__main__":
    main()
