# Ambiente Virtual - Conni Robot

## Como ativar o ambiente virtual

### No Windows (PowerShell):
```powershell
# Ativar o ambiente virtual
.\venv\Scripts\Activate.ps1

# Ou se houver problemas de política de execução:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### No Windows (CMD):
```cmd
# Ativar o ambiente virtual
venv\Scripts\activate.bat
```

### No Linux/Mac:
```bash
# Ativar o ambiente virtual
source venv/bin/activate
```

## Instalar dependências

Após ativar o ambiente virtual, instale as dependências:

```bash
pip install -r requirements.txt
```

## Desativar o ambiente virtual

```bash
deactivate
```

## Estrutura do projeto

- `Conni_virtual_face/` - Interface visual do robo (tkinter)
- `Conni_vision/` - Reconhecimento facial (OpenCV)
- `Conni_voice/` - Processamento de voz (Vosk)
- `Conni_move/` - Controle de movimento (PlatformIO)

## Dependências principais

- **opencv-python**: Visão computacional e detecção facial
- **numpy**: Processamento numérico
- **vosk**: Reconhecimento de voz offline
- **pygame**: Reprodução de áudio
- **openai**: Integração com IA
- **pyaudio**: Captura de áudio do microfone
