#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo Completo - FM888 com Face Tracking
Demonstra todas as funcionalidades do sensor FM888
"""

from fm import FM
import time
import sys

class ExemploFM888:
    """Classe para demonstrar funcionalidades do FM888"""
    
    def __init__(self, porta: str = "COM11"):
        self.sensor = FM(porta)
        self.porta = porta
    
    def conectar(self):
        """Conecta e inicializa o sensor"""
        try:
            print(f"🔌 Conectando na porta {self.porta}...")
            self.sensor.reset()
            time.sleep(1)
            
            status = self.sensor.get_status()
            print(f"✅ Conectado! Status: {status}")
            return True
            
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")
            return False
    
    def desconectar(self):
        """Desconecta o sensor"""
        try:
            self.sensor.close()
            print("🔌 Desconectado")
        except:
            pass
    
    def _explicar_erro(self, codigo: int):
        """Explica o significado dos códigos de erro"""
        erros = {
            1: "❌ Erro de comunicação",
            2: "❌ Erro de hardware", 
            3: "❌ Erro de firmware",
            4: "❌ Erro de parâmetros",
            5: "❌ Erro de timeout",
            6: "❌ Erro de memória",
            7: "❌ Erro de dados",
            8: "❌ Face não reconhecida (usuário não cadastrado)",
            9: "❌ Erro de qualidade da imagem",
            10: "❌ Erro de posicionamento da face"
        }
        
        explicacao = erros.get(codigo, f"❌ Erro desconhecido (código {codigo})")
        print(f"   {explicacao}")
        
        if codigo == 8:
            print("   💡 Dica: Cadastre um usuário primeiro (opção 3)")
        elif codigo == 9:
            print("   💡 Dica: Melhore a iluminação e posicionamento")
        elif codigo == 10:
            print("   💡 Dica: Centralize o rosto na câmera")
    
    def verificar_face_streaming(self):
        """Verificação com streaming de dados em tempo real"""
        print("\n🔍 VERIFICAÇÃO COM STREAMING")
        print("=" * 50)
        print("Posicione seu rosto na frente do sensor...")
        print("Pressione Ctrl+C para parar")
        print("-" * 50)
        
        try:
            while True:
                # Verifica se sensor está pronto
                if not self.sensor.is_verify_ready():
                    print("⏳ Aguardando sensor ficar pronto...")
                    time.sleep(0.5)
                    continue
                
                print("\n🚀 Enviando comando verify...")
                
                # Usa streaming - dados conforme chegam
                for data in self.sensor.verify(timeout_s=10, show_face_tracking=True):
                    if data["type"] == "face_tracking":
                        # Dados de face em tempo real
                        face = data["face_info"]
                        print(f"👤 Face: state={face['state']}, bbox={face['bbox']}")
                        
                    elif data["type"] == "reply":
                        # Resposta final
                        if data["ok"]:
                            print(f"✅ SUCESSO! Usuário: {data.get('user_name', 'N/A')}")
                            print(f"   ID: {data.get('user_id', 'N/A')}")
                            print(f"   Admin: {data.get('admin', False)}")
                        else:
                            print(f"❌ FALHOU: código {data.get('code')}")
                        print(f"📊 Frames coletados: {len(data['face_data'])}")
                        break
                        
                    elif data["type"] == "error":
                        print(f"❌ ERRO: Código {data.get('code', 'N/A')}")
                        self._explicar_erro(data.get('code', 0))
                        print(f"📊 Frames coletados: {len(data.get('face_data', []))}")
                        break
                        
                    elif data["type"] == "timeout":
                        print(f"⏰ TIMEOUT: {data}")
                        break
                
                print("✅ Verificação concluída. Aguardando 2s...")
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n⏹️ Parado pelo usuário")
    
    def verificar_face_simples(self):
        """Verificação simples (compatibilidade)"""
        print("\n🔍 VERIFICAÇÃO SIMPLES")
        print("=" * 50)
        
        try:
            # Usa verify_sync - funciona como antes
            result = self.sensor.verify_sync(timeout_s=10, show_face_tracking=True)
            
            print(f"Resultado: {result}")
            
            if result.get('ok'):
                print(f"✅ SUCESSO! Usuário: {result.get('user_name', 'N/A')}")
                print(f"   ID: {result.get('user_id', 'N/A')}")
                print(f"   Admin: {result.get('admin', False)}")
                print(f"📊 Frames coletados: {len(result.get('face_data', []))}")
            else:
                print(f"❌ FALHOU: {result.get('error', 'Erro desconhecido')}")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def cadastrar_usuario(self):
        """Cadastra novo usuário"""
        print("\n📝 CADASTRO DE USUÁRIO")
        print("=" * 50)
        
        nome = input("Digite o nome do usuário: ").strip()
        if not nome:
            print("❌ Nome não pode estar vazio")
            return
        
        admin = input("É administrador? (s/n): ").strip().lower() == 's'
        
        try:
            print(f"📝 Cadastrando usuário: {nome}")
            user_id = self.sensor.enroll(nome, admin=admin, show_face_tracking=True)
            print(f"✅ Usuário cadastrado com sucesso! ID: {user_id}")
            
        except Exception as e:
            print(f"❌ Erro no cadastro: {e}")
    
    def apagar_usuario(self):
        """Apaga usuário específico"""
        print("\n🗑️ APAGAR USUÁRIO")
        print("=" * 50)
        
        try:
            user_id = int(input("Digite o ID do usuário: "))
            self.sensor.delete_user(user_id)
            print(f"✅ Usuário {user_id} removido com sucesso!")
            
        except ValueError:
            print("❌ ID deve ser um número")
        except Exception as e:
            print(f"❌ Erro ao apagar: {e}")
    
    def apagar_todos(self):
        """Apaga todos os usuários"""
        print("\n🗑️ APAGAR TODOS OS USUÁRIOS")
        print("=" * 50)
        
        confirmacao = input("Tem certeza? Digite 'CONFIRMAR': ").strip()
        if confirmacao != "CONFIRMAR":
            print("❌ Operação cancelada")
            return
        
        try:
            self.sensor.delete_all()
            print("✅ Todos os usuários removidos!")
            
        except Exception as e:
            print(f"❌ Erro ao apagar: {e}")
    
    def configurar_sensor(self):
        """Configura o sensor"""
        print("\n⚙️ CONFIGURAÇÃO DO SENSOR")
        print("=" * 50)
        
        try:
            # Configura UVC
            print("📹 Configurando câmera UVC...")
            self.sensor.config_uvc(usb=0x20, quality=75, mirror=False, rot180=False)
            
            # Configura níveis
            print("🔧 Configurando níveis...")
            self.sensor.set_rgb_level(2)
            self.sensor.set_face_box(True)
            
            print("✅ Sensor configurado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro na configuração: {e}")
    
    def verificar_usuarios(self):
        """Verifica se há usuários cadastrados"""
        print("\n👥 VERIFICAR USUÁRIOS CADASTRADOS")
        print("=" * 50)
        
        try:
            # Tenta fazer uma verificação simples para ver se há usuários
            print("🔍 Testando verificação...")
            result = self.sensor.verify_sync(timeout_s=5, show_face_tracking=False)
            
            if result.get('ok'):
                print(f"✅ Usuário encontrado: {result.get('user_name', 'N/A')}")
                print(f"   ID: {result.get('user_id', 'N/A')}")
                print(f"   Admin: {result.get('admin', False)}")
            else:
                codigo = result.get('code', 0)
                print(f"❌ Nenhum usuário reconhecido (código: {codigo})")
                self._explicar_erro(codigo)
                
        except Exception as e:
            print(f"❌ Erro ao verificar usuários: {e}")
    
    def mostrar_menu(self):
        """Mostra menu principal"""
        print("\n" + "="*60)
        print("🤖 EXEMPLO FM888 - FACE TRACKING")
        print("="*60)
        print("1. Verificação com Streaming (tempo real)")
        print("2. Verificação Simples (compatibilidade)")
        print("3. Cadastrar Usuário")
        print("4. Apagar Usuário")
        print("5. Apagar Todos os Usuários")
        print("6. Verificar Usuários Cadastrados")
        print("7. Configurar Sensor")
        print("8. Sair")
        print("-"*60)
    
    def executar(self):
        """Executa o exemplo principal"""
        if not self.conectar():
            return
        
        try:
            while True:
                self.mostrar_menu()
                opcao = input("Escolha uma opção: ").strip()
                
                if opcao == "1":
                    self.verificar_face_streaming()
                elif opcao == "2":
                    self.verificar_face_simples()
                elif opcao == "3":
                    self.cadastrar_usuario()
                elif opcao == "4":
                    self.apagar_usuario()
                elif opcao == "5":
                    self.apagar_todos()
                elif opcao == "6":
                    self.verificar_usuarios()
                elif opcao == "7":
                    self.configurar_sensor()
                elif opcao == "8":
                    print("👋 Saindo...")
                    break
                else:
                    print("❌ Opção inválida")
                
                input("\nPressione Enter para continuar...")
                
        except KeyboardInterrupt:
            print("\n⏹️ Interrompido pelo usuário")
        
        finally:
            self.desconectar()

def main():
    """Função principal"""
    print("🤖 Exemplo FM888 - Face Tracking")
    print("="*40)
    
    # Pede porta se não fornecida
    porta = input("Digite a porta serial (padrão: COM11): ").strip()
    if not porta:
        porta = "COM11"
    
    # Cria e executa exemplo
    exemplo = ExemploFM888(porta)
    exemplo.executar()

if __name__ == "__main__":
    main()
