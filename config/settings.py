# settings.py - Gerenciador de configurações do Conni Robot
# Requisitos: pip install json

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

class ConfigManager:
    """Classe flexível para gerenciar todas as configurações do Conni Robot"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
        
        # Configurações padrão do sistema
        self.default_configs = {
            "camera": {
                "width": 640,
                "height": 480,
                "fps": 30,
                "brightness": 0,
                "contrast": 0,
                "saturation": 0
            },
            "detection": {
                "scale_factor": 1.1,
                "min_neighbors": 5,
                "min_size": [30, 30],
                "avg_face_width_cm": 14.0,
                "confidence_threshold": 0.5
            },
            "calibration": {
                "focal_length": 500.0,
                "calibrated": False,
                "calibration_date": None,
                "calibration_distance_cm": None
            },
            "voice": {
                "enabled": True,
                "language": "pt-BR",
                "volume": 0.8,
                "speed": 1.0,
                "voice_id": "default"
            },
            "movement": {
                "enabled": True,
                "max_speed": 100,
                "acceleration": 50,
                "smooth_movement": True
            },
            "behavior": {
                "greeting_enabled": True,
                "auto_tracking": True,
                "interaction_timeout": 30,
                "sleep_mode_timeout": 300
            },
            "sensors": {
                "ultrasonic_enabled": True,
                "infrared_enabled": True,
                "touch_enabled": True,
                "battery_monitoring": True
            },
            "network": {
                "wifi_enabled": True,
                "bluetooth_enabled": True,
                "server_port": 8080,
                "api_enabled": True
            }
        }
    
    def get_config_file_path(self, config_name: str) -> str:
        """Retorna o caminho do arquivo de configuração"""
        return os.path.join(self.config_dir, f"{config_name}.json")
    
    def load_config(self, config_name: str = "conni_config") -> Dict[str, Any]:
        """Carrega configurações de um arquivo específico"""
        config_file = self.get_config_file_path(config_name)
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Para arquivos específicos, não mesclar com padrões
                if config_name == "conni_config":
                    return self._merge_configs(self.default_configs, config)
                else:
                    return config
            else:
                # Retornar configurações padrão apenas para conni_config
                if config_name == "conni_config":
                    return self.default_configs.copy()
                else:
                    return {}
        except Exception as e:
            print(f"Erro ao carregar configurações {config_name}: {e}")
            if config_name == "conni_config":
                return self.default_configs.copy()
            else:
                return {}
    
    def save_config(self, config: Dict[str, Any], config_name: str = "conni_config") -> bool:
        """Salva configurações em um arquivo específico"""
        config_file = self.get_config_file_path(config_name)
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✓ Configurações {config_name} salvas")
            return True
        except Exception as e:
            print(f"Erro ao salvar configurações {config_name}: {e}")
            return False
    
    def get_config_value(self, key_path: str, config_name: str = "conni_config") -> Any:
        """Obtém um valor específico das configurações usando notação de ponto"""
        config = self.load_config(config_name)
        keys = key_path.split('.')
        value = config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return None
    
    def set_config_value(self, key_path: str, value: Any, config_name: str = "conni_config") -> bool:
        """Define um valor específico nas configurações usando notação de ponto"""
        config = self.load_config(config_name)
        keys = key_path.split('.')
        
        try:
            # Navegar até o penúltimo nível
            current = config
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Definir o valor final
            current[keys[-1]] = value
            
            return self.save_config(config, config_name)
        except Exception as e:
            print(f"Erro ao definir valor {key_path}: {e}")
            return False
    
    def update_config_section(self, section: str, updates: Dict[str, Any], 
                             config_name: str = "conni_config") -> bool:
        """Atualiza uma seção específica das configurações"""
        config = self.load_config(config_name)
        
        if section not in config:
            config[section] = {}
        
        config[section].update(updates)
        return self.save_config(config, config_name)
    
    def add_new_config_section(self, section: str, config_data: Dict[str, Any], 
                              config_name: str = "conni_config") -> bool:
        """Adiciona uma nova seção de configurações"""
        config = self.load_config(config_name)
        config[section] = config_data
        return self.save_config(config, config_name)
    
    def remove_config_section(self, section: str, config_name: str = "conni_config") -> bool:
        """Remove uma seção de configurações"""
        config = self.load_config(config_name)
        if section in config:
            del config[section]
            return self.save_config(config, config_name)
        return True
    
    def list_config_sections(self, config_name: str = "conni_config") -> List[str]:
        """Lista todas as seções de configurações"""
        config = self.load_config(config_name)
        return list(config.keys())
    
    def reset_config_to_default(self, config_name: str = "conni_config") -> bool:
        """Reseta configurações para valores padrão"""
        return self.save_config(self.default_configs, config_name)
    
    def backup_config(self, config_name: str = "conni_config", backup_suffix: str = None) -> bool:
        """Cria backup das configurações"""
        if backup_suffix is None:
            backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_file = self.get_config_file_path(f"{config_name}_backup_{backup_suffix}")
        config = self.load_config(config_name)
        
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✓ Backup criado: {backup_file}")
            return True
        except Exception as e:
            print(f"Erro ao criar backup: {e}")
            return False
    
    def restore_config_from_backup(self, backup_file: str, config_name: str = "conni_config") -> bool:
        """Restaura configurações de um backup"""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return self.save_config(config, config_name)
        except Exception as e:
            print(f"Erro ao restaurar backup: {e}")
            return False
    
    # Métodos específicos para calibração (compatibilidade)
    def load_calibration(self) -> Dict[str, Any]:
        """Carrega dados de calibração (método de compatibilidade)"""
        try:
            return self.load_config("calibration")
        except Exception as e:
            print(f"Erro ao carregar calibração: {e}")
            # Retornar calibração padrão em caso de erro
            return {
                "focal_length": 500.0,
                "calibrated": False,
                "calibration_date": "",
                "calibration_distance_cm": 0,
                "face_width_at_calibration": 0
            }
    
    def save_calibration(self, focal_length: float, calibration_distance_cm: float, 
                        face_width_pixels: int) -> bool:
        """Salva dados de calibração (método de compatibilidade)"""
        calibration_data = {
            "focal_length": focal_length,
            "calibrated": True,
            "calibration_date": datetime.now().isoformat(),
            "calibration_distance_cm": calibration_distance_cm,
            "face_width_at_calibration": face_width_pixels
        }
        
        success = self.save_config(calibration_data, "calibration")
        if success:
            print(f"✓ Calibração salva: Distância focal = {focal_length:.2f}")
        return success
    
    def reset_calibration(self) -> bool:
        """Reseta a calibração para valores padrão (método de compatibilidade)"""
        calibration_data = {
            "focal_length": 500.0,
            "calibrated": False,
            "calibration_date": None,
            "calibration_distance_cm": None,
            "face_width_at_calibration": None
        }
        
        success = self.save_config(calibration_data, "calibration")
        if success:
            print("✓ Calibração resetada para valores padrão")
        return success
    
    def get_calibration_info(self) -> str:
        """Retorna informações da calibração atual (método de compatibilidade)"""
        calibration = self.load_calibration()
        
        if calibration.get("calibrated", False):
            return (f"Calibração ativa - Distância focal: {calibration['focal_length']:.2f}\n"
                   f"Data: {calibration['calibration_date']}\n"
                   f"Distância de calibração: {calibration['calibration_distance_cm']}cm")
        else:
            return "Nenhuma calibração salva - Usando valores padrão"
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Mescla configurações carregadas com padrões"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

# Instância global do gerenciador de configurações
config_manager = ConfigManager()

# Funções de conveniência para compatibilidade
def get_config() -> Dict[str, Any]:
    """Função de conveniência para obter configurações principais"""
    return config_manager.load_config("conni_config")

def get_calibration() -> Dict[str, Any]:
    """Função de conveniência para obter calibração"""
    return config_manager.load_calibration()

def save_calibration(focal_length: float, calibration_distance_cm: float, 
                    face_width_pixels: int) -> bool:
    """Função de conveniência para salvar calibração"""
    return config_manager.save_calibration(focal_length, calibration_distance_cm, face_width_pixels)

# Novas funções de conveniência para configurações flexíveis
def get_robot_config(config_name: str = "conni_config") -> Dict[str, Any]:
    """Obtém configurações de qualquer módulo do robô"""
    return config_manager.load_config(config_name)

def set_robot_config_value(key_path: str, value: Any, config_name: str = "conni_config") -> bool:
    """Define um valor específico nas configurações do robô"""
    return config_manager.set_config_value(key_path, value, config_name)

def get_robot_config_value(key_path: str, config_name: str = "conni_config") -> Any:
    """Obtém um valor específico das configurações do robô"""
    return config_manager.get_config_value(key_path, config_name)

def update_robot_config_section(section: str, updates: Dict[str, Any], 
                               config_name: str = "conni_config") -> bool:
    """Atualiza uma seção específica das configurações do robô"""
    return config_manager.update_config_section(section, updates, config_name)

def add_robot_config_section(section: str, config_data: Dict[str, Any], 
                            config_name: str = "conni_config") -> bool:
    """Adiciona uma nova seção de configurações do robô"""
    return config_manager.add_new_config_section(section, config_data, config_name)

def backup_robot_config(config_name: str = "conni_config") -> bool:
    """Cria backup das configurações do robô"""
    return config_manager.backup_config(config_name)
