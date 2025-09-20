"""
Teste do FM888 com Face Tracking Integrado
Demonstra o uso dos métodos verify() e enroll() com face tracking em tempo real
Verificação em loop contínuo até pressionar 'q'
"""

from fm import FM
import time

def testar_verificacao_loop_continuo():
    """Testa verificação com face tracking em loop contínuo"""
    print("🔍 Teste de Verificação em Loop Contínuo")
    print("=" * 60)
    print("Pressione Ctrl+C para parar")
    print("=" * 60)
    
    # Cria objeto conectado na porta serial
    sensor = FM(port="COM11", baudrate=115200)
    
    try:
        # Inicializa o sensor
        print("🔄 Resetando sensor...")
        sensor.reset()
        print("✅ Sensor resetado com sucesso")
        
        # Verifica status inicial
        print("\n📊 Verificando status...")
        status = sensor.get_status()
        print(f"Status: {status} (0=IDLE, 1=BUSY, 2=ERROR, 3=INVALID)")
        
        print("\n🔍 Iniciando verificação em loop contínuo...")
        print("Posicione seu rosto na frente do sensor...")
        
        verificacao_count = 0
        
        while True:
            try:
                result = sensor.verify_sync(timeout_s=10, show_face_tracking=True)  # Ativar debug
                # Analisa dados de face
                face_data = result.get('face_data', [])
                
                if face_data:
                    print("✅ Face box detectado!")
                    print(f"  Sucesso: {result.get('ok', False)}")
                    print(f"  Usuário: {result.get('user_name', 'N/A')}")
                    print(f"  ID: {result.get('user_id', 'N/A')}")
                    print(f"  Frames com face box: {len(face_data)}")
                    
                    # Mostra detalhes dos dados de face
                    for i, face in enumerate(face_data):
                        state = face['state']
                        bbox = face['bbox']
                        print(f"  Frame {i+1}: state={state}, bbox={bbox}")
                else:
                    print("❌ Nenhum face box detectado")
                             
            except KeyboardInterrupt:
                print("\n⏹️ Interrompido pelo usuário (Ctrl+C)")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")
                print("⏳ Aguardando 3 segundos...")
                time.sleep(3.0)
        
        print(f"\n📊 Estatísticas finais:")
        print(f"  Total de verificações: {verificacao_count}")
        print("✅ Loop finalizado")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        sensor.close()
        print("\n🔌 Conexão fechada")

def testar_verificacao_com_face_tracking():
    """Testa verificação com face tracking integrado"""
    print("🔍 Teste de Verificação com Face Tracking")
    print("=" * 60)
    
    sensor = FM(port="COM11", baudrate=115200)
    
    try:
        # Inicializa o sensor
        print("🔄 Resetando sensor...")
        sensor.reset()
        print("✅ Sensor resetado")
        
        # Verifica status
        print("\n📊 Verificando status...")
        status = sensor.get_status()
        print(f"Status: {status} (0=IDLE, 1=BUSY, 2=ERROR, 3=INVALID)")
        
        # Executa verificação
        print("\n🔍 Executando verificação...")
        print("Posicione seu rosto na frente do sensor...")
        
        result = sensor.verify_sync(timeout_s=10, show_face_tracking=True)
        
        # Mostra resultado
        print("\n📊 Resultado:")
        print(f"  Sucesso: {result.get('ok', False)}")
        print(f"  Usuário: {result.get('user_name', 'N/A')}")
        print(f"  ID: {result.get('user_id', 'N/A')}")
        print(f"  Frames coletados: {len(result.get('face_data', []))}")
        
        # Analisa dados de face
        face_data = result.get('face_data', [])
        if face_data:
            faces_detectadas = [f for f in face_data if f['state'] > 0]
            print(f"  Faces detectadas: {len(faces_detectadas)}/{len(face_data)} frames")
            
            if faces_detectadas:
                # Calcula área média
                areas = []
                for face in faces_detectadas:
                    bbox = face['bbox']
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    areas.append(width * height)
                
                area_media = sum(areas) / len(areas)
                print(f"  Área média: {area_media:.0f} pixels²")
                
                if area_media > 50000:
                    print("  ✅ Face de boa qualidade")
                elif area_media > 20000:
                    print("  ⚠️ Face de qualidade média")
                else:
                    print("  ❌ Face de baixa qualidade")
        
        return result
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None
    finally:
        sensor.close()
        print("\n🔌 Conexão fechada")

def testar_cadastro_com_face_tracking():
    """Testa cadastro com face tracking integrado"""
    print("📝 Teste de Cadastro com Face Tracking")
    print("=" * 60)
    
    sensor = FM(port="COM11", baudrate=115200)
    
    try:
        # Reset do sensor
        print("🔄 Resetando sensor...")
        sensor.reset()
        
        # Cadastro com face tracking
        print("\n📝 Executando cadastro...")
        print("Posicione seu rosto na frente do sensor...")
        
        user_id = sensor.enroll(
            name="UsuarioTeste", 
            admin=False, 
            timeout_s=15, 
            show_face_tracking=True
        )
        
        print(f"✅ Usuário cadastrado! ID: {user_id}")
        
        # Testa verificação
        print("\n🔍 Testando verificação...")
        result = sensor.verify_sync(timeout_s=10, show_face_tracking=True)
        
        if result.get('ok'):
            print(f"✅ Usuário verificado: {result.get('user_name')}")
        else:
            print(f"❌ Falha na verificação: {result.get('code')}")
        
        # Limpa usuário de teste
        print(f"\n🗑️ Removendo usuário de teste...")
        sensor.delete_user(user_id)
        print("✅ Usuário removido")
        
        return user_id
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None
    finally:
        sensor.close()
        print("\n🔌 Conexão fechada")

def testar_face_tracking_standalone():
    """Testa face tracking standalone"""
    print("🎯 Teste de Face Tracking Standalone")
    print("=" * 60)
    
    sensor = FM(port="COM11", baudrate=115200)
    
    try:
        # Reset do sensor
        print("🔄 Resetando sensor...")
        sensor.reset()
        
        # Inicia verificação em background
        print("🔍 Iniciando verificação...")
        sensor._send(0x12, bytes([0, 10]))  # VERIFY
        
        # Face tracking standalone
        print("📊 Iniciando face tracking...")
        print("Pressione Ctrl+C para parar")
        
        frame_count = 0
        start_time = time.time()
        
        try:
            for face_info in sensor.face_tracking():
                frame_count += 1
                current_time = time.time() - start_time
                
                state = face_info['state']
                bbox = face_info['bbox']
                
                status_icon = "👤" if state > 0 else "👁️"
                print(f"{status_icon} Frame {frame_count:3d} | {current_time:5.1f}s | Estado: {state:2d}")
                
                if state > 0:
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    area = width * height
                    print(f"    📐 Tamanho: {width}x{height} (área: {area})")
                
                # Para após 30 segundos
                if current_time > 30:
                    print("⏰ Timeout de 30 segundos atingido")
                    break
                    
        except KeyboardInterrupt:
            print("\n⏹️ Face tracking interrompido")
        
        print(f"\n📊 Estatísticas:")
        print(f"  Frames processados: {frame_count}")
        print(f"  Tempo total: {time.time() - start_time:.1f}s")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        sensor.close()
        print("\n🔌 Conexão fechada")

def testar_apagar_todos_usuarios():
    """Testa apagar todos os usuários"""
    print("🗑️ Teste de Apagar Todos os Usuários")
    print("=" * 60)
    
    sensor = FM(port="COM11", baudrate=115200)
    
    try:
        # Reset do sensor
        print("🔄 Resetando sensor...")
        sensor.reset()
        
        # Verifica quantos usuários existem antes
        print("\n📊 Verificando usuários existentes...")
        try:
            user_count = sensor.get_user_count()
            print(f"Usuários cadastrados: {user_count}")
        except:
            print("⚠️ Não foi possível verificar quantidade de usuários")
        
        # Apaga todos os usuários
        print("\n🗑️ Apagando todos os usuários...")
        result = sensor.delete_all()
        
        if result:
            print("✅ Todos os usuários foram apagados com sucesso!")
        else:
            print("❌ Erro ao apagar usuários")
        
        # Verifica quantos usuários restaram
        print("\n📊 Verificando usuários restantes...")
        try:
            user_count = sensor.get_user_count()
            print(f"Usuários restantes: {user_count}")
        except:
            print("⚠️ Não foi possível verificar quantidade de usuários")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        sensor.close()
        print("\n🔌 Conexão fechada")

if __name__ == "__main__":
    print("🚀 Teste Completo do FM888 com Face Tracking Integrado")
    print("=" * 80)
    
    # Menu de opções
    print("\nEscolha o teste:")
    print("1. Verificação com face tracking integrado")
    print("2. Verificação em loop contínuo")
    print("3. Cadastro com face tracking integrado")
    print("4. Face tracking standalone")
    print("5. Apagar todos os usuários")
    print("6. Todos os testes")
    
    try:
        opcao = input("\nDigite sua opção (1-6): ").strip()
        
        if opcao == "1":
            testar_verificacao_com_face_tracking()
        elif opcao == "2":
            testar_verificacao_loop_continuo()
        elif opcao == "3":
            testar_cadastro_com_face_tracking()
        elif opcao == "4":
            testar_face_tracking_standalone()
        elif opcao == "5":
            testar_apagar_todos_usuarios()
        elif opcao == "6":
            testar_verificacao_com_face_tracking()
            testar_cadastro_com_face_tracking()
            testar_face_tracking_standalone()
        else:
            print("❌ Opção inválida")
            
    except KeyboardInterrupt:
        print("\n⏹️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n✅ Teste concluído!")
