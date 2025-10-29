import numpy as np
import librosa
import sounddevice as sd
import soundfile as sf
import os
import json
from datetime import datetime
from collections import deque

# Arquivo JSON para armazenar comandos e características
COMANDOS_FILE = "comandos.json"


def carregar_comandos():
    """Carrega comandos e suas características do arquivo JSON"""
    try:
        if os.path.exists(COMANDOS_FILE):
            with open(COMANDOS_FILE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            return dados
        else:
            # Cria arquivo inicial se não existir
            dados_iniciais = {}
            salvar_comandos(dados_iniciais)
            return dados_iniciais
    except Exception as e:
        print(f"Erro ao carregar comandos: {e}")
        return {}

def salvar_comandos(dados):
    """Salva comandos e características no arquivo JSON"""
    try:
        with open(COMANDOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar comandos: {e}")
        return False

def adicionar_comando(nome_comando, caracteristicas):
    """Adiciona um novo comando com suas características"""
    dados = carregar_comandos()
    if nome_comando not in dados:
        dados[nome_comando] = {
            "caracteristicas": caracteristicas,
            "data_criacao": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "amostras": len(caracteristicas)
        }
        if salvar_comandos(dados):
            print(f"✅ Comando '{nome_comando}' adicionado com {len(caracteristicas)} amostras!")
            return True
        else:
            print(f"❌ Erro ao salvar comando '{nome_comando}'")
            return False
    else:
        print(f"⚠️ Comando '{nome_comando}' já existe!")
        return False

def remover_comando(nome_comando):
    """Remove um comando da lista"""
    dados = carregar_comandos()
    if nome_comando in dados:
        del dados[nome_comando]
        if salvar_comandos(dados):
            print(f"✅ Comando '{nome_comando}' removido!")
            return True
        else:
            print(f"❌ Erro ao salvar alterações")
            return False
    else:
        print(f"❌ Comando '{nome_comando}' não encontrado!")
        return False

def listar_comandos():
    """Lista todos os comandos cadastrados com suas características"""
    dados = carregar_comandos()
    if dados:
        print(f"\n📋 COMANDOS CADASTRADOS ({len(dados)}):")
        for i, (cmd, info) in enumerate(dados.items(), 1):
            amostras = info.get("amostras", 0)
            data_criacao = info.get("data_criacao", "N/A")
            print(f"  {i:2d}. ✅ {cmd} ({amostras} amostras, criado em: {data_criacao})")
    else:
        print("\n📋 Nenhum comando cadastrado!")
    return dados

def carregar_referencias():
    """Carrega as características dos comandos do JSON"""
    referencias = {}
    dados = carregar_comandos()
    
    for cmd, info in dados.items():
        caracteristicas = info.get("caracteristicas", [])
        if caracteristicas:
            # Converte de volta para numpy arrays
            amostras_comando = [np.array(car) for car in caracteristicas]
            referencias[cmd] = amostras_comando
            print(f"📚 Comando '{cmd}': {len(amostras_comando)} amostras carregadas")
        else:
            print(f"❌ Nenhuma característica válida encontrada para: {cmd}")
    
    return referencias


def detectar_fala_continuo(
    taxa=16000,
    janela=0.05,
    nivel_minimo=0.015,
    inicio_minimo=4,
    silencio_limite=12,
    pre_buffer=1.0,
    pasta="gravacoes"
): 
    bloco_tamanho = int(taxa * janela)
    pre_frames = int(pre_buffer / janela)
    pre_audio = deque(maxlen=pre_frames)

    buffer = []
    cont_voz = 0
    cont_silencio = 0
    gravando = False
    terminou = False

    print("🎤 Microfone ativo — pronto para detectar fala.")

    def callback(indata, frames, time_info, status):
        nonlocal cont_voz, cont_silencio, gravando, terminou

        if status:
            print(status)

        # normaliza e calcula energia RMS
        energia = np.sqrt(np.mean(indata ** 2))
        pre_audio.append(indata.copy())  # pré-grava tudo

        if energia > nivel_minimo:
            cont_voz += 1
            cont_silencio = 0
        else:
            cont_silencio += 1

        # dispara gravação depois de voz estável
        if not gravando and cont_voz >= inicio_minimo:
            gravando = True
            print("🎙️ Iniciando gravação...")
            buffer.extend(list(pre_audio))  # inclui o áudio anterior
            pre_audio.clear()

        # durante a gravação
        if gravando:
            buffer.append(indata.copy())
            if cont_silencio >= silencio_limite:
                terminou = True

    # 🔹 abre stream ANTES da detecção (pré-stream ativo)
    stream = sd.InputStream(
        callback=callback,
        channels=1,
        samplerate=taxa,
        blocksize=bloco_tamanho,
    )
    stream.start()

    # aguarda até o final da fala
    while not terminou:
        sd.sleep(int(janela * 1000))

    stream.stop()
    stream.close()

    if not buffer:
        print("❌ Nenhum áudio gravado.")
        return None, None

    # achata blocos e garante formato correto
    audio = np.concatenate([b.flatten() for b in buffer])
    # Garante que o áudio seja 1D e do tipo correto
    audio = audio.flatten().astype(np.float32)

    return audio

def reconhecer_comando(audio, referencias, threshold=50):
    """Reconhece o comando baseado na distância euclidiana (compara com múltiplas amostras)"""
    # Extrai características do áudio gravado
    sr = 16000
    y = librosa.util.normalize(audio)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    
    # Calcula média e desvio padrão
    media = np.mean(mfcc, axis=1)
    std = np.std(mfcc, axis=1)
    features = np.concatenate([media, std])
    
    # Calcula distância entre o áudio e cada comando (múltiplas amostras)
    distancias_comandos = {}
    distancias_detalhadas = {}
    
    for cmd, amostras in referencias.items():
        distancias_amostras = []
        
        # Calcula distância para cada amostra do comando
        for i, amostra in enumerate(amostras):
            distancia = np.linalg.norm(features - amostra)
            distancias_amostras.append(distancia)
        
        # Usa a menor distância entre as amostras do comando
        menor_distancia_comando = min(distancias_amostras)
        distancias_comandos[cmd] = menor_distancia_comando
        distancias_detalhadas[cmd] = distancias_amostras
    
    # Encontra o comando com menor distância
    melhor_comando = min(distancias_comandos, key=distancias_comandos.get)
    menor_distancia = distancias_comandos[melhor_comando]
    
    # Verifica se a distância está abaixo do limiar
    if menor_distancia < threshold:
        return melhor_comando, menor_distancia, distancias_detalhadas
    else:
        return "comando_nao_reconhecido", menor_distancia, distancias_detalhadas

def gravar_comando(nome, duracao=2, taxa=16000):
    """Grava 3 amostras de um novo comando de referência"""
    print(f"🎤 Gravando 3 amostras do comando '{nome}'...")
    
    caracteristicas_comando = []
    
    for i in range(1, 4):  # Grava 3 amostras
        print(f"\n--- Amostra {i}/3 ---")
        print("3...")
        import time
        time.sleep(1)
        print("2...")
        time.sleep(1)
        print("1...")
        time.sleep(1)
        print("GRAVANDO!")
        
        try:
            audio = detectar_fala_continuo()
            
            if audio is None:
                print(f"❌ Erro ao gravar amostra {i}!")
                continue
            
            # Extrai características diretamente do áudio gravado
            sr = 16000
            y = librosa.util.normalize(audio)
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # Calcula média e desvio padrão
            media = np.mean(mfcc, axis=1)
            std = np.std(mfcc, axis=1)
            features = np.concatenate([media, std])
            
            # Converte para lista para salvar no JSON
            caracteristicas_comando.append(features.tolist())
            print(f"✅ Amostra {i} processada e características extraídas!")
                
        except Exception as e:
            print(f"❌ Erro ao processar amostra {i}: {e}")
    
    if caracteristicas_comando:
        # Adiciona o comando com suas características
        if adicionar_comando(nome, caracteristicas_comando):
            print(f"\n🎉 Comando '{nome}' gravado com {len(caracteristicas_comando)}/3 amostras!")
            return True
        else:
            print(f"\n❌ Erro ao salvar comando '{nome}'!")
            return False
    else:
        print(f"\n❌ Falha ao gravar comando '{nome}'!")
        return False

def testar_comando_audio(audio, referencias, threshold=50):
    """Testa um comando específico usando áudio direto"""
    if audio is None:
        print(f"❌ Áudio inválido!")
        return
    
    print(f"🧪 Testando áudio gravado...")
    
    # Reconhece o comando
    comando, distancia, todas_distancias = reconhecer_comando(audio, referencias, threshold)
    
    print(f"📊 Resultado:")
    print(f"  Comando reconhecido: {comando}")
    print(f"  Distância: {distancia:.2f}")
    print(f"  Limiar: {threshold}")
    
    print(f"\n📈 Distâncias detalhadas:")
    for cmd, distancias_amostras in todas_distancias.items():
        status = "✅" if cmd == comando else "❌"
        dist_min = min(distancias_amostras)
        print(f"  {status} {cmd}: {dist_min:.2f} (amostras: {[f'{d:.1f}' for d in distancias_amostras]})")

def menu_principal():
    """Menu interativo para o sistema"""
    print("=== SISTEMA DE RECONHECIMENTO DE COMANDOS (CARACTERÍSTICAS JSON) ===")
    
    # Carrega referências
    referencias = carregar_referencias()
    
    # Limiar de distância padrão
    threshold = 30
    
    if referencias:
        print(f"\n📚 Comandos disponíveis: {list(referencias.keys())}")
    else:
        print(f"\n📋 Nenhum comando cadastrado ainda.")
        print("💡 Use a opção 2 para gravar seu primeiro comando!")
    
    while True:
        print("\nEscolha uma opção:")
        print("1. Reconhecer comando (tempo real)")
        print("2. Gravar novo comando")
        print("3. Testar arquivo específico")
        print("4. Ajustar limiar de distância")
        print("5. Listar comandos cadastrados")
        print("6. Remover comando")
        print("7. Mostrar estatísticas")
        print("8. Sair")
        
        escolha = input("\nDigite sua escolha (1-8): ").strip()
        
        if escolha == "1":
            if not referencias:
                print("\n❌ Nenhum comando cadastrado!")
                print("💡 Use a opção 2 para gravar comandos primeiro.")
                continue
            
            print("\n🎤 Gravando comando...")
            audio = detectar_fala_continuo()
            
            if audio is None:
                print("❌ Erro ao gravar áudio!")
                continue
            
            # Salva temporariamente para análise
            temp_file = f"temp_{datetime.now().strftime('%H%M%S')}.wav"
            sf.write(temp_file, audio, 16000)
            
            comando, distancia, todas_distancias = reconhecer_comando(audio, referencias, threshold)
            
            print(f"\n🔊 Resultado:")
            print(f"  Comando: {comando}")
            print(f"  Distância: {distancia:.2f}")
            
            if comando != "comando_nao_reconhecido":
                print(f"✅ Comando reconhecido: {comando}")
            else:
                print(f"❌ Comando não reconhecido (distância muito alta)")
            
            # Remove arquivo temporário
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        elif escolha == "2":
            nome = input("Digite o nome do comando: ").strip()
            if nome:
                if gravar_comando(nome):
                    # Recarrega referências após gravar com sucesso
                    referencias = carregar_referencias()
                    print(f"📚 Comandos disponíveis: {list(referencias.keys())}")
        
        elif escolha == "3":
            if not referencias:
                print("\n❌ Nenhum comando cadastrado!")
                print("💡 Use a opção 2 para gravar comandos primeiro.")
                continue
            
            print("\n🎤 Gravando áudio para teste...")
            audio = detectar_fala_continuo()
            
            if audio is None:
                print("❌ Erro ao gravar áudio!")
                continue
            
            testar_comando_audio(audio, referencias, threshold)
        
        elif escolha == "4":
            print(f"\n📊 Limiar atual: {threshold}")
            print("Limiar menor = mais sensível (mais falsos positivos)")
            print("Limiar maior = menos sensível (pode perder comandos)")
            print("Recomendado: 30-80")
            
            novo_limiar = input("Novo limiar (Enter para manter): ").strip()
            if novo_limiar:
                try:
                    threshold = float(novo_limiar)
                    print(f"✅ Limiar atualizado para: {threshold}")
                except ValueError:
                    print("❌ Valor inválido!")
        
        elif escolha == "5":
            listar_comandos()
        
        elif escolha == "6":
            print("\n🗑️ REMOVER COMANDO")
            dados_disponiveis = carregar_comandos()
            if dados_disponiveis:
                print("Comandos disponíveis para remoção:")
                for i, cmd in enumerate(dados_disponiveis.keys(), 1):
                    print(f"  {i}. {cmd}")
                
                try:
                    indice = int(input("\nDigite o número do comando para remover: ")) - 1
                    comandos_lista = list(dados_disponiveis.keys())
                    if 0 <= indice < len(comandos_lista):
                        comando_para_remover = comandos_lista[indice]
                        confirmacao = input(f"Tem certeza que deseja remover '{comando_para_remover}'? (s/N): ").strip().lower()
                        if confirmacao in ['s', 'sim', 'y', 'yes']:
                            remover_comando(comando_para_remover)
                            # Recarrega referências após remoção
                            referencias = carregar_referencias()
                        else:
                            print("Remoção cancelada.")
                    else:
                        print("❌ Número inválido!")
                except ValueError:
                    print("❌ Digite um número válido!")
            else:
                print("❌ Nenhum comando cadastrado para remover!")
        
        elif escolha == "7":
            print(f"\n📈 Estatísticas:")
            dados_cadastrados = carregar_comandos()
            print(f"  Comandos cadastrados: {len(dados_cadastrados)}")
            print(f"  Referências carregadas: {len(referencias)}")
            print(f"  Limiar de distância: {threshold}")
            print(f"  Comandos e amostras:")
            for cmd, info in dados_cadastrados.items():
                amostras = info.get("amostras", 0)
                data_criacao = info.get("data_criacao", "N/A")
                print(f"    ✅ {cmd}: {amostras} amostras (criado em: {data_criacao})")
        
        elif escolha == "8":
            print("👋 Saindo...")
            break
        
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    menu_principal()
