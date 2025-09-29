# config/__init__.py - Pacote de configurações do Conni Robot
# Este pacote contém o sistema flexível de configurações para todos os módulos do robô

from .settings import (
    ConfigManager,
    config_manager,
    get_config,
    get_calibration,
    save_calibration,
    get_robot_config,
    set_robot_config_value,
    get_robot_config_value,
    update_robot_config_section,
    add_robot_config_section,
    backup_robot_config
)

__version__ = "1.0.0"
__author__ = "Conni Robot Team"

__all__ = [
    "ConfigManager",
    "config_manager",
    "get_config",
    "get_calibration", 
    "save_calibration",
    "get_robot_config",
    "set_robot_config_value",
    "get_robot_config_value",
    "update_robot_config_section",
    "add_robot_config_section",
    "backup_robot_config"
]

