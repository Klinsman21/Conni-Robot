# Pasta de Configurações - Conni Robot

Esta pasta contém arquivos de configuração flexíveis para todos os módulos do Conni Robot.

## Arquivos

### `conni_config.json`
Configurações principais do sistema:
- **camera**: Configurações da câmera (resolução, FPS, brilho, contraste)
- **detection**: Parâmetros de detecção de faces
- **voice**: Configurações de voz e fala
- **movement**: Configurações de movimento e servos
- **behavior**: Comportamentos e interações
- **sensors**: Configurações de sensores
- **network**: Configurações de rede

### `calibration.json`
Dados de calibração da câmera:
- **focal_length**: Distância focal calculada
- **calibrated**: Se a câmera foi calibrada
- **calibration_date**: Data da calibração
- **calibration_distance_cm**: Distância usada na calibração
- **face_width_at_calibration**: Largura da face em pixels na calibração

### `*_module.json`
Configurações específicas de módulos (ex: `voice_module.json`, `movement_module.json`)

## API Flexível

### Uso Básico
```python
from config.settings import config_manager

# Carregar configurações
config = config_manager.load_config("conni_config")

# Obter valor específico
camera_width = config_manager.get_config_value("camera.width")

# Definir valor específico
config_manager.set_config_value("camera.brightness", 10)
```

### Configurações por Módulo
```python
# Configurações específicas do módulo de voz
voice_config = {
    "enabled": True,
    "language": "pt-BR",
    "volume": 0.9,
    "speed": 1.2
}
config_manager.save_config(voice_config, "voice_module")

# Carregar configurações do módulo
voice_settings = config_manager.load_config("voice_module")
```

### Atualização de Seções
```python
# Atualizar seção específica
sensor_updates = {
    "ultrasonic_enabled": True,
    "battery_monitoring": True
}
config_manager.update_config_section("sensors", sensor_updates)
```

### Nova Seção de Configurações
```python
# Adicionar nova seção
ai_config = {
    "model_path": "models/conni_ai_v1.0",
    "confidence_threshold": 0.7,
    "learning_enabled": True
}
config_manager.add_new_config_section("ai", ai_config)
```

### Backup e Restauração
```python
# Criar backup
config_manager.backup_config("conni_config")

# Restaurar de backup
config_manager.restore_config_from_backup("backup_file.json")
```

### Notação de Ponto
```python
# Acessar valores aninhados
volume = config_manager.get_config_value("voice.volume")
timeout = config_manager.get_config_value("behavior.interaction_timeout")

# Definir valores aninhados
config_manager.set_config_value("camera.resolution.width", 1920)
config_manager.set_config_value("ai.speech_recognition.language", "pt-BR")
```

## Exemplo Completo

Execute o exemplo para ver todas as funcionalidades:
```bash
python exemplo_config_flexivel.py
```

## Métodos Disponíveis

### ConfigManager
- `load_config(config_name)`: Carrega configurações
- `save_config(config, config_name)`: Salva configurações
- `get_config_value(key_path, config_name)`: Obtém valor específico
- `set_config_value(key_path, value, config_name)`: Define valor específico
- `update_config_section(section, updates, config_name)`: Atualiza seção
- `add_new_config_section(section, config_data, config_name)`: Adiciona seção
- `remove_config_section(section, config_name)`: Remove seção
- `list_config_sections(config_name)`: Lista seções
- `backup_config(config_name)`: Cria backup
- `restore_config_from_backup(backup_file, config_name)`: Restaura backup

### Funções de Conveniência
- `get_robot_config(config_name)`: Obtém configurações
- `set_robot_config_value(key_path, value, config_name)`: Define valor
- `get_robot_config_value(key_path, config_name)`: Obtém valor
- `update_robot_config_section(section, updates, config_name)`: Atualiza seção
- `add_robot_config_section(section, config_data, config_name)`: Adiciona seção
- `backup_robot_config(config_name)`: Cria backup

## Backup

É recomendado fazer backup desta pasta antes de atualizações importantes, pois contém todas as configurações específicas do seu robô.
