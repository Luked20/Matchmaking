import socketio
import logging
import sys
import time
import random

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClienteMatchmaking:
    def __init__(self, server_url: str = "http://localhost:5000"):
        self.sio = socketio.Client()
        self.server_url = server_url
        self.nickname = f"Jogador_{random.randint(1000, 9999)}"
        self.elo = random.randint(1000, 5000)
        self.em_fila = False
        
        # Configura os eventos
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('error', self.on_error)
        self.sio.on('match_encontrado', self.on_match_encontrado)
        
        # Tentativa de conexão com retry
        self.conectar_com_retry()
        
        # Faz login automático
        self.login()
    
    def conectar_com_retry(self, max_tentativas=5, intervalo=2):
        for tentativa in range(max_tentativas):
            try:
                logger.info(f"Tentando conectar ao servidor (tentativa {tentativa + 1}/{max_tentativas})...")
                self.sio.connect(self.server_url)
                logger.info("Conexão estabelecida com sucesso!")
                return
            except Exception as e:
                logger.error(f"Erro na conexão: {e}")
                if tentativa < max_tentativas - 1:
                    logger.info(f"Aguardando {intervalo} segundos antes da próxima tentativa...")
                    time.sleep(intervalo)
                else:
                    logger.error("Número máximo de tentativas excedido. Encerrando...")
                    sys.exit(1)
    
    def login(self):
        try:
            logger.info(f"Login automático como {self.nickname} com elo {self.elo}")
            self.sio.emit('login', {
                'nickname': self.nickname,
                'elo': self.elo
            })
        except Exception as e:
            logger.error(f"Erro ao fazer login: {e}")
    
    def on_connect(self):
        logger.info("Conectado ao servidor")
    
    def on_disconnect(self):
        logger.info("Desconectado do servidor")
    
    def on_error(self, data):
        logger.error(f"Erro: {data['message']}")
    
    def on_match_encontrado(self, data):
        logger.info("\n=== RESULTADO DA PARTIDA ===")
        logger.info(f"Você jogou contra: {data['jogador2']}")
        logger.info(f"Vencedor: {data['vencedor']}")
        logger.info("\nSua performance:")
        logger.info(f"Kills: {data['kills_j1']}")
        logger.info(f"Deaths: {data['deaths_j1']}")
        logger.info(f"Assists: {data['assists_j1']}")
        logger.info(f"Tempo da partida: {data['tempo_partida']} minutos")
        logger.info(f"Ping médio: {data['ping']:.1f}ms")
        logger.info("===========================\n")
        self.em_fila = False
    
    def entrar_fila(self):
        try:
            if not self.em_fila:
                logger.info("Entrando na fila de matchmaking...")
                self.em_fila = True
                self.sio.emit('entrar_fila')
            else:
                logger.info("Você já está na fila!")
        except Exception as e:
            logger.error(f"Erro ao entrar na fila: {e}")
    
    def sair_fila(self):
        try:
            if self.em_fila:
                logger.info("Saindo da fila de matchmaking...")
                self.em_fila = False
                self.sio.emit('sair_fila')
            else:
                logger.info("Você não está na fila!")
        except Exception as e:
            logger.error(f"Erro ao sair da fila: {e}")

def main():
    try:
        logger.info("Iniciando cliente de matchmaking...")
        cliente = ClienteMatchmaking()
        
        while True:
            print("\nOpções:")
            print("1. Entrar na fila")
            print("2. Sair da fila")
            print("3. Sair")
            
            opcao = input("Escolha uma opção: ")
            
            if opcao == '1':
                cliente.entrar_fila()
                # Aguarda o match ser encontrado
                while cliente.em_fila:
                    time.sleep(60)
            elif opcao == '2':
                cliente.sair_fila()
            elif opcao == '3':
                logger.info("Encerrando cliente...")
                break
            else:
                logger.error("Opção inválida!")
    
    except KeyboardInterrupt:
        logger.info("Cliente encerrado pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")

if __name__ == "__main__":
    main() 