# fm.py - Biblioteca para módulos FM22x/FM888/AI-10/50 (Fuge)
# Requisitos: pip install pyserial

import serial
import struct
import time
from typing import Optional, Dict, Generator

# =============================================================================
# CONSTANTES DO PROTOCOLO
# =============================================================================

# Sincronização de pacotes
SYNC = b"\xEF\xAA"

# Comandos (Host -> Módulo)
RESET = 0x10
GET_STATUS = 0x11
VERIFY = 0x12
ENROLL_SINGLE = 0x1D
DELUSER = 0x20
DELALL = 0x21
SET_USB_UVC = 0xB1
SET_FACE_BOX = 0xB5
RGB_LEVEL = 0xD4

# Tipos de resposta (Módulo -> Host)
MID_REPLY = 0x00  # Resposta de comando
MID_NOTE = 0x01   # Notificação/streaming

# IDs de notificação
NID_READY = 0
NID_FACE_STATE = 1

# Códigos de resultado
MR_SUCCESS = 0

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def _xor(data: bytes) -> int:
    """Calcula checksum XOR de um conjunto de bytes"""
    result = 0
    for byte in data:
        result ^= byte
    return result & 0xFF

def _be16(value: int) -> bytes:
    """Converte inteiro para 2 bytes em big-endian"""
    return struct.pack(">H", value)

def _u16(high: int, low: int) -> int:
    """Converte 2 bytes para inteiro de 16 bits"""
    return ((high & 0xFF) << 8) | (low & 0xFF)

class FMError(Exception):
    """Exceção para erros do módulo FM"""
    pass

# =============================================================================
# CLASSE PRINCIPAL
# =============================================================================

class FM:
    """
    Cliente para módulos de reconhecimento facial FM22x/FM888/AI-10/50
    
    Exemplo de uso:
        fm = FM('COM11')
        fm.reset()
        result = fm.verify()
        if result['ok']:
            print(f"Usuário: {result['user_name']}")
        fm.close()
    """
    
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.2, read_timeout: float = 3.0):
        """
        Inicializa conexão com o módulo
        
        Args:
            port: Porta serial (ex: 'COM11', '/dev/ttyUSB0')
            baudrate: Velocidade da comunicação
            timeout: Timeout para escrita
            read_timeout: Timeout para leitura
        """
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        self.read_timeout = read_timeout

    # =========================================================================
    # COMUNICAÇÃO SERIAL
    # =========================================================================
    
    def _send(self, command: int, data: bytes = b""):
        """Envia comando para o módulo"""
        size = _be16(len(data))
        frame = SYNC + bytes([command]) + size + data
        checksum = _xor(frame[2:])
        frame += bytes([checksum])
        
        self.ser.write(frame)
        self.ser.flush()

    def _read_exact(self, n_bytes: int) -> bytes:
        """Lê exatamente n_bytes da porta serial"""
        buffer = bytearray()
        start_time = time.time()
        
        while len(buffer) < n_bytes:
            if time.time() - start_time > self.read_timeout:
                raise FMError(f"Timeout lendo {n_bytes} bytes")
            
            chunk = self.ser.read(n_bytes - len(buffer))
            if chunk:
                buffer.extend(chunk)
        
        return bytes(buffer)

    def _receive_packet(self) -> Dict:
        """Recebe e decodifica um pacote do módulo"""
        # Busca sincronização
        sync = self._read_exact(2)
        while sync != SYNC:
            sync = sync[1:] + self._read_exact(1)
        
        # Lê cabeçalho
        message_id = self._read_exact(1)[0]
        size = struct.unpack(">H", self._read_exact(2))[0]
        data = self._read_exact(size)
        checksum = self._read_exact(1)[0]
        
        # Verifica checksum
        expected_checksum = _xor(bytes([message_id]) + _be16(size) + data)
        if checksum != expected_checksum:
            raise FMError("Checksum inválido")
        
        # Decodifica tipo de pacote
        if message_id == MID_REPLY:
            if size < 2:
                raise FMError("REPLY muito curto")
            return {
                "type": "REPLY",
                "mid": data[0],
                "result": data[1],
                "data": data[2:]
            }
        elif message_id == MID_NOTE:
            if size < 1:
                raise FMError("NOTE muito curto")
            return {
                "type": "NOTE",
                "nid": data[0],
                "data": data[1:]
            }
        else:
            return {
                "type": "IMAGE",
                "mid": message_id,
                "data": data
            }

    def _wait_reply(self, expected_command: int, require_success: bool = True) -> Dict:
        """Aguarda resposta de um comando específico"""
        start_time = time.time()
        
        while True:
            packet = self._receive_packet()
            
            if packet["type"] == "REPLY" and packet["mid"] == expected_command:
                if require_success and packet["result"] != MR_SUCCESS:
                    raise FMError(f"Comando 0x{expected_command:02X} falhou: código {packet['result']}")
                return packet
            
            # Ignora outros tipos de pacote
            if time.time() - start_time > self.read_timeout + 2:
                raise FMError("Timeout aguardando resposta")

    # =========================================================================
    # COMANDOS BÁSICOS
    # =========================================================================
    
    def reset(self):
        """Reinicia o módulo"""
        self._send(RESET)
        self._wait_reply(RESET, require_success=False)

    def get_status(self) -> int:
        """
        Obtém status do módulo
        
        Returns:
            0=IDLE, 1=BUSY, 2=ERROR, 3=INVALID
        """
        self._send(GET_STATUS)
        reply = self._wait_reply(GET_STATUS)
        return reply["data"][0] if reply["data"] else -1

    def close(self):
        """Fecha conexão serial"""
        try:
            self.ser.close()
        except:
            pass

    # =========================================================================
    # CONFIGURAÇÃO
    # =========================================================================
    
    def config_uvc(self, usb: int = 0x20, quality: int = 75, mirror: bool = False, 
                   rot180: bool = False, bitrate_mbps: Optional[int] = None, 
                   fm226_or_ai: bool = True):
        """
        Configura interface UVC (câmera USB)
        
        Args:
            usb: Modo USB
            quality: Qualidade (10-100)
            mirror: Espelhar imagem
            rot180: Rotacionar 180°
            bitrate_mbps: Taxa de bits em Mbps
            fm226_or_ai: Se é FM226/AI-10/50
        """
        attr = (1 if mirror else 0) | ((1 if rot180 else 0) << 1)
        
        if fm226_or_ai:
            payload = bytes([usb & 0xFF, (bitrate_mbps or 24) & 0xFF, quality & 0xFF, attr & 0xFF])
        else:
            payload = bytes([usb & 0xFF, attr & 0xFF, quality & 0xFF])
        
        self._send(SET_USB_UVC, payload)
        self._wait_reply(SET_USB_UVC)

    def set_face_box(self, enable: bool):
        """Habilita/desabilita caixa de face"""
        self._send(SET_FACE_BOX, bytes([1 if enable else 0]))
        self._wait_reply(SET_FACE_BOX)

    def set_rgb_level(self, level: int = 2):
        """
        Define nível de segurança RGB
        
        Args:
            level: 0-4 (0 ~ 1e-5 FAR; 2 ~ 1e-7 FAR)
        """
        self._send(RGB_LEVEL, bytes([level & 0xFF, 0x00]))
        self._wait_reply(RGB_LEVEL)

    # =========================================================================
    # VERIFICAÇÃO FACIAL
    # =========================================================================
    
    def verify(self, timeout_s: int = 10, powerdown_after_ok: bool = False, 
               show_face_tracking: bool = False) -> Generator[Dict, None, None]:
        """
        Executa verificação facial com streaming de dados
        
        Args:
            timeout_s: Timeout em segundos
            powerdown_after_ok: Desligar após sucesso
            show_face_tracking: Mostrar dados de face tracking
            
        Yields:
            Dict com dados conforme chegam (REPLY ou face tracking)
        """
        self._send(VERIFY, bytes([int(powerdown_after_ok) & 0xFF, int(timeout_s) & 0xFF]))
        
        if show_face_tracking:
            print("📊 Face tracking ativado")
            print("=" * 50)
        
        face_data = []
        start_time = time.time()
        verification_complete = False
        
        while time.time() - start_time < timeout_s + 2 and not verification_complete:
            try:
                packet = self._receive_packet()
                
                if packet["type"] == "REPLY" and packet["mid"] == VERIFY:
                    # Resposta da verificação
                    if packet["result"] != MR_SUCCESS:
                        yield {"type": "error", "ok": False, "code": packet["result"], "face_data": face_data}
                        return
                    
                    data = packet["data"]
                    result = {"type": "reply", "ok": True, "face_data": face_data}
                    
                    # Extrai dados do usuário se disponíveis
                    if len(data) >= 36:
                        user_id = _u16(data[0], data[1])
                        name = bytes(data[2:34]).split(b"\x00", 1)[0].decode(errors="ignore")
                        admin = data[34]
                        unlock = data[35]
                        result.update({
                            "user_id": user_id,
                            "user_name": name,
                            "admin": admin,
                            "unlockStatus": unlock
                        })
                    yield result
                    verification_complete = True
                
                elif packet["type"] == "NOTE" and packet.get("nid") == NID_FACE_STATE:
                    # Dados de face tracking
                    face_info = self._process_face_tracking_data(packet["data"], face_data, start_time, show_face_tracking)
                    if face_info:
                        yield {"type": "face_tracking", "face_info": face_info, "face_data": face_data}
                
            except FMError as e:
                if "timeout" in str(e).lower():
                    break
                raise
        
        if not verification_complete:
            yield {"type": "timeout", "ok": False, "code": -1, "face_data": face_data, "error": "timeout"}

    def verify_sync(self, timeout_s: int = 10, powerdown_after_ok: bool = False, 
                   show_face_tracking: bool = False) -> Dict:
        """
        Versão síncrona da verificação (compatibilidade com código existente)
        
        Args:
            timeout_s: Timeout em segundos
            powerdown_after_ok: Desligar após sucesso
            show_face_tracking: Mostrar dados de face tracking
            
        Returns:
            Dict com resultado final da verificação
        """
        result = None
        for data in self.verify(timeout_s, powerdown_after_ok, show_face_tracking):
            if data["type"] in ["reply", "error", "timeout"]:
                result = data
                break
        return result or {"ok": False, "code": -1, "face_data": [], "error": "no_response"}

    def _process_face_tracking_data(self, data: bytes, face_data: list, start_time: float, show_debug: bool) -> Optional[Dict]:
        """Processa dados de face tracking"""
        if len(data) >= 16:
            # Verifica se há face detectada (primeiro byte = 0x00)
            if data[0] == 0x00:
                # Desempacota dados de face
                values = struct.unpack("<8h", data[:16])
                state, left, top, right, bottom, yaw, pitch, roll = values
                
                face_info = {
                    "state": state,
                    "bbox": (left, top, right, bottom),
                    "yaw": yaw,
                    "pitch": pitch,
                    "roll": roll,
                    "timestamp": time.time() - start_time
                }
                face_data.append(face_info)
                
                if show_debug:
                    self._print_face_info(face_info)
                
                return face_info
        return None

    def _print_face_info(self, face_info: Dict):
        """Imprime informações de face tracking"""
        state = face_info["state"]
        bbox = face_info["bbox"]
        yaw, pitch, roll = face_info["yaw"], face_info["pitch"], face_info["roll"]
        timestamp = face_info["timestamp"]
        
        icon = "👤" if state > 0 else "👁️"
        bbox_str = f"({bbox[0]:3d}, {bbox[1]:3d}, {bbox[2]:3d}, {bbox[3]:3d})"
        angles_str = f"Y:{yaw:3d}° P:{pitch:3d}° R:{roll:3d}°"
        time_str = f"{timestamp:5.1f}s"
        
        print(f"{icon} {time_str} | Estado: {state:2d} | BBox: {bbox_str} | Ângulos: {angles_str}")
        
        if state > 0:
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            area = width * height
            center_x = (bbox[0] + bbox[2]) // 2
            center_y = (bbox[1] + bbox[3]) // 2
            print(f"    📐 Tamanho: {width}x{height} (área: {area}) | Centro: ({center_x}, {center_y})")

    # =========================================================================
    # CADASTRO DE USUÁRIOS
    # =========================================================================
    
    def enroll(self, name: str, admin: bool = False, timeout_s: int = 10, 
               show_face_tracking: bool = False) -> int:
        """
        Cadastra novo usuário
        
        Args:
            name: Nome do usuário
            admin: Se é administrador
            timeout_s: Timeout em segundos
            show_face_tracking: Mostrar dados de face tracking
            
        Returns:
            ID do usuário cadastrado
        """
        # Prepara nome (32 bytes, preenchido com zeros)
        name_bytes = name.encode()[:32]
        name_bytes = name_bytes + b"\x00" * (32 - len(name_bytes))
        
        payload = bytes([1 if admin else 0]) + name_bytes + bytes([0, int(timeout_s) & 0xFF])
        self._send(ENROLL_SINGLE, payload)
        
        print(f"📝 Cadastrando usuário: {name}")
        
        if show_face_tracking:
            print("📊 Face tracking ativado")
            print("=" * 50)
        
        face_data = []
        start_time = time.time()
        
        while time.time() - start_time < timeout_s + 2:
            try:
                packet = self._receive_packet()
                
                if packet["type"] == "REPLY" and packet["mid"] == ENROLL_SINGLE:
                    if packet["result"] != MR_SUCCESS:
                        raise FMError(f"Cadastro falhou: código {packet['result']}")
                    
                    data = packet["data"]
                    if len(data) >= 2:
                        user_id = _u16(data[0], data[1])
                        
                        if show_face_tracking:
                            print("=" * 50)
                            print(f"✅ Usuário cadastrado! ID: {user_id}")
                            print(f"📊 Frames coletados: {len(face_data)}")
                        
                        return user_id
                    else:
                        raise FMError("Resposta de cadastro inválida")
                
                elif packet["type"] == "NOTE" and packet.get("nid") == NID_FACE_STATE:
                    self._process_face_tracking_data(packet["data"], face_data, start_time, show_face_tracking)
                
            except FMError as e:
                if "timeout" in str(e).lower():
                    break
                raise
        
        raise FMError("Timeout durante cadastro")

    # =========================================================================
    # GERENCIAMENTO DE USUÁRIOS
    # =========================================================================
    
    def delete_user(self, user_id: int):
        """Remove usuário específico"""
        self._send(DELUSER, bytes([(user_id >> 8) & 0xFF, user_id & 0xFF]))
        self._wait_reply(DELUSER)

    def delete_all(self):
        """Remove todos os usuários"""
        self._send(DELALL)
        self._wait_reply(DELALL)

    def get_user_count(self) -> int:
        """Obtém quantidade de usuários cadastrados"""
        # Implementação básica - pode ser expandida conforme necessário
        return 0

    def is_verify_ready(self) -> bool:
        """
        Verifica se o sensor está pronto para um novo comando verify
        
        Returns:
            True se pronto, False se ainda processando
        """
        try:
            # Tenta ler um pacote sem timeout longo
            original_timeout = self.ser.timeout
            self.ser.timeout = 0.1
            
            packet = self._receive_packet()
            
            # Verifica se é o pacote de conclusão: EF AA 00 00 02 12 08 18
            if (packet["type"] == "REPLY" and 
                packet["mid"] == VERIFY and 
                packet["result"] == 0x08 and
                len(packet["data"]) >= 1 and 
                packet["data"][0] == 0x18):
                return True
                
        except (FMError, serial.SerialTimeoutException):
            # Timeout ou erro = sensor não está enviando dados = pronto
            return True
        except:
            # Outros erros = não pronto
            return False
        finally:
            self.ser.timeout = original_timeout
        
        return False

    # =========================================================================
    # FACE TRACKING
    # =========================================================================
    
    def face_tracking(self) -> Generator[Dict, None, None]:
        """
        Gerador para face tracking contínuo
        
        Yields:
            Dict com dados de face: state, bbox, yaw, pitch, roll
        """
        self.ser.reset_input_buffer()
        
        while True:
            packet = self._receive_packet()
            
            if packet["type"] == "NOTE" and packet.get("nid") == NID_FACE_STATE:
                data = packet["data"]
                if len(data) >= 16:
                    values = struct.unpack("<8h", data[:16])
                    state, left, top, right, bottom, yaw, pitch, roll = values
                    
                    yield {
                        "state": state,
                        "bbox": (left, top, right, bottom),
                        "yaw": yaw,
                        "pitch": pitch,
                        "roll": roll
                    }

# =============================================================================
# EXEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cliente FM888")
    parser.add_argument("--port", required=True, help="Porta serial")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate")
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos")
    
    # Comando reset
    subparsers.add_parser("reset", help="Reinicia módulo")
    
    # Comando status
    subparsers.add_parser("status", help="Obtém status")
    
    # Comando verify
    verify_parser = subparsers.add_parser("verify", help="Verificação facial")
    verify_parser.add_argument("--timeout", type=int, default=10, help="Timeout em segundos")
    verify_parser.add_argument("--tracking", action="store_true", help="Mostrar face tracking")
    
    # Comando enroll
    enroll_parser = subparsers.add_parser("enroll", help="Cadastro de usuário")
    enroll_parser.add_argument("--name", required=True, help="Nome do usuário")
    enroll_parser.add_argument("--admin", action="store_true", help="Usuário administrador")
    enroll_parser.add_argument("--tracking", action="store_true", help="Mostrar face tracking")
    
    # Comando delete
    delete_parser = subparsers.add_parser("delete", help="Remove usuário")
    delete_parser.add_argument("--uid", type=int, required=True, help="ID do usuário")
    
    # Comando delete all
    subparsers.add_parser("deleteall", help="Remove todos os usuários")
    
    # Comando config
    config_parser = subparsers.add_parser("config", help="Configura módulo")
    config_parser.add_argument("--mirror", action="store_true", help="Espelhar imagem")
    config_parser.add_argument("--rot180", action="store_true", help="Rotacionar 180°")
    config_parser.add_argument("--quality", type=int, default=75, help="Qualidade (10-100)")
    
    # Comando track
    subparsers.add_parser("track", help="Face tracking contínuo")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        exit(1)
    
    # Executa comando
    fm = FM(args.port, args.baud)
    
    try:
        if args.command == "reset":
            fm.reset()
            print("✅ Módulo reiniciado")
            
        elif args.command == "status":
            status = fm.get_status()
            status_names = {0: "IDLE", 1: "BUSY", 2: "ERROR", 3: "INVALID"}
            print(f"Status: {status} ({status_names.get(status, 'UNKNOWN')})")
            
        elif args.command == "verify":
            if args.tracking:
                # Modo streaming - mostra dados conforme chegam
                print("📊 Modo streaming ativado")
                for data in fm.verify(timeout_s=args.timeout, show_face_tracking=True):
                    if data["type"] == "face_tracking":
                        print(f"👤 Face: {data['face_info']}")
                    elif data["type"] == "reply":
                        print(f"✅ Resultado final: {data}")
                    elif data["type"] == "error":
                        print(f"❌ Erro: {data}")
                    elif data["type"] == "timeout":
                        print(f"⏰ Timeout: {data}")
            else:
                # Modo síncrono - compatibilidade
                result = fm.verify_sync(timeout_s=args.timeout, show_face_tracking=False)
                print(f"Resultado: {result}")
            
        elif args.command == "enroll":
            user_id = fm.enroll(args.name, admin=args.admin, show_face_tracking=args.tracking)
            print(f"✅ Usuário cadastrado! ID: {user_id}")
            
        elif args.command == "delete":
            fm.delete_user(args.uid)
            print(f"✅ Usuário {args.uid} removido")
            
        elif args.command == "deleteall":
            fm.delete_all()
            print("✅ Todos os usuários removidos")
            
        elif args.command == "config":
            fm.config_uvc(mirror=args.mirror, rot180=args.rot180, quality=args.quality)
            fm.set_rgb_level(2)
            fm.set_face_box(True)
            print("✅ Módulo configurado")
            
        elif args.command == "track":
            print("📊 Face tracking ativo (Ctrl+C para parar)")
            try:
                for face_info in fm.face_tracking():
                    print(face_info)
            except KeyboardInterrupt:
                print("\n⏹️ Face tracking interrompido")
    
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    finally:
        fm.close()