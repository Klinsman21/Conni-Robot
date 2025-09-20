# FM888 - Face Tracking

## 📋 Visão Geral

Biblioteca Python para módulos de reconhecimento facial FM22x/FM888/AI-10/50 com suporte a face tracking em tempo real.

## 🚀 Instalação

```bash
pip install pyserial
```

## 📁 Arquivos

- **`fm.py`** - Biblioteca principal
- **`exemplo_fm888.py`** - Exemplo completo
- **`teste_face_tracking_integrado.py`** - Teste integrado
- **`teste_direto_uvc.py`** - Teste com câmera UVC

## 🎯 Funcionalidades

### Verificação Facial
- **Streaming**: Dados em tempo real
- **Síncrona**: Compatibilidade com código existente
- **Face Tracking**: Detecção e rastreamento de faces

### Gerenciamento de Usuários
- Cadastro de usuários
- Remoção de usuários
- Listagem de usuários

### Configuração
- Interface UVC (câmera)
- Níveis de segurança
- Parâmetros de detecção

## 🔧 Uso Básico

### Conexão
```python
from fm import FM

sensor = FM('COM11')  # Ajuste a porta
sensor.reset()
```

### Verificação Simples
```python
# Modo síncrono (compatibilidade)
result = sensor.verify_sync(timeout_s=10, show_face_tracking=True)
if result['ok']:
    print(f"Usuário: {result['user_name']}")
```

### Verificação com Streaming
```python
# Modo streaming (tempo real)
for data in sensor.verify(timeout_s=10, show_face_tracking=True):
    if data["type"] == "face_tracking":
        print(f"Face: {data['face_info']}")
    elif data["type"] == "reply":
        print(f"Resultado: {data}")
        break
```

### Cadastro de Usuário
```python
user_id = sensor.enroll("João", admin=False, show_face_tracking=True)
print(f"Usuário cadastrado: {user_id}")
```

## 🎮 Exemplo Interativo

Execute o exemplo completo:

```bash
python exemplo_fm888.py
```

Menu disponível:
1. Verificação com Streaming (tempo real)
2. Verificação Simples (compatibilidade)
3. Cadastrar Usuário
4. Apagar Usuário
5. Apagar Todos os Usuários
6. Configurar Sensor
7. Sair

## 📊 Tipos de Dados

### Face Tracking
```python
{
    "state": 1,                    # Estado da face
    "bbox": (100, 50, 200, 150),  # Bounding box
    "yaw": 5,                      # Rotação Y
    "pitch": -2,                   # Rotação X
    "roll": 1,                     # Rotação Z
    "timestamp": 2.5               # Timestamp
}
```

### Resultado da Verificação
```python
{
    "ok": True,                    # Sucesso
    "user_id": 123,               # ID do usuário
    "user_name": "João",          # Nome do usuário
    "admin": False,               # É administrador
    "unlockStatus": 1,            # Status de desbloqueio
    "face_data": [...]            # Dados de face coletados
}
```

## ⚙️ Configuração

### UVC (Câmera)
```python
sensor.config_uvc(usb=0x20, quality=75, mirror=False, rot180=False)
```

### Níveis de Segurança
```python
sensor.set_rgb_level(2)  # 0-4 (2 = 1e-7 FAR)
```

### Face Box
```python
sensor.set_face_box(True)  # Habilita caixa de face
```

## 🔍 Controle de Comandos

### Verificar se Sensor Está Pronto
```python
if sensor.is_verify_ready():
    # Sensor pronto para novo comando
    for data in sensor.verify(timeout_s=10):
        # Processa dados...
```

## 📝 Notas Importantes

- **Porta Serial**: Ajuste conforme seu sistema (COM11, /dev/ttyUSB0, etc.)
- **Timeout**: Comando verify dura 10 segundos por padrão
- **Face Tracking**: Primeiro byte = 0x00 indica face detectada
- **Compatibilidade**: Use `verify_sync()` para código existente

## 🐛 Solução de Problemas

### Erro de Conexão
- Verifique a porta serial
- Confirme se o sensor está conectado
- Teste com `sensor.get_status()`

### Face Não Detectada
- Verifique iluminação
- Posicione rosto centralizado
- Ajuste níveis de segurança

### Timeout
- Aumente `timeout_s` se necessário
- Verifique se sensor está funcionando
- Use `is_verify_ready()` para controle

## 📞 Suporte

Para dúvidas ou problemas, verifique:
1. Logs de erro no console
2. Status do sensor com `get_status()`
3. Configuração da porta serial
4. Iluminação e posicionamento
