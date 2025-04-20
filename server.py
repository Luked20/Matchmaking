from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from database import Database
from ia_matchmaking import SistemaIA
import json
from typing import Dict, List, Optional
import time
import threading
import sys
import logging
import random
from datetime import datetime, timedelta
from game import Partida
import signal
import eventlet
eventlet.monkey_patch()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Configuração do SocketIO com eventlet
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25
)
db = Database()
sistema_ia = SistemaIA()

# Dicionário para armazenar os sockets ativos
sockets_ativos: Dict[str, str] = {}  # {socket_id: nickname}
# Dicionário para armazenar os jogadores
jogadores: Dict[str, Dict] = {}
# Lista de jogadores na fila com seus tempos de entrada
fila: Dict[str, datetime] = {}

def calcular_novo_elo(elo_vencedor: int, elo_perdedor: int) -> tuple[int, int]:
    """Calcula o novo elo após uma partida usando o sistema Elo"""
    K = 32  # Fator K (quanto mais alto, mais o elo muda)
    
    # Calcula a probabilidade esperada de vitória
    esperado_vencedor = 1 / (1 + 10 ** ((elo_perdedor - elo_vencedor) / 400))
    esperado_perdedor = 1 - esperado_vencedor
    
    # Calcula o novo elo
    novo_elo_vencedor = elo_vencedor + K * (1 - esperado_vencedor)
    novo_elo_perdedor = elo_perdedor + K * (0 - esperado_perdedor)
    
    return int(novo_elo_vencedor), int(novo_elo_perdedor)

def encontrar_match(jogador1: str) -> Optional[str]:
    """Encontra um match adequado para o jogador usando clustering"""
    if len(fila) < 2:
        return None
    
    # Busca o jogador1 no banco
    jogador1_data = db.buscar_jogador(jogador1)
    if not jogador1_data:
        logger.error(f"Jogador {jogador1} não encontrado no banco")
        return None
    
    # Busca todos os jogadores na fila
    jogadores_na_fila = []
    for nickname in fila:
        if nickname != jogador1:
            jogador = db.buscar_jogador(nickname)
            if jogador:
                jogadores_na_fila.append(jogador)
    
    if not jogadores_na_fila:
        return None
    
    # Usa o sistema de IA para agrupar os jogadores
    grupos = sistema_ia.agrupar_jogadores([jogador1_data] + jogadores_na_fila)
    
    # Encontra o grupo do jogador1
    grupo_jogador1 = None
    for grupo, membros in grupos.items():
        if any(m['nickname'] == jogador1 for m in membros):
            grupo_jogador1 = grupo
            break
    
    if grupo_jogador1 is None:
        return None
    
    # Procura o melhor match no mesmo grupo
    melhor_match = None
    menor_diferenca_elo = float('inf')
    
    for jogador in grupos[grupo_jogador1]:
        if jogador['nickname'] != jogador1 and jogador['nickname'] in fila:
            diferenca_elo = abs(jogador1_data['estatisticas']['elo'] - jogador['estatisticas']['elo'])
            if diferenca_elo < menor_diferenca_elo:
                melhor_match = jogador['nickname']
                menor_diferenca_elo = diferenca_elo
    
    if melhor_match:
        logger.info(f"Match encontrado usando clustering: {jogador1} vs {melhor_match}")
        logger.info(f"Grupo: {grupo_jogador1}")
        logger.info(f"Diferença de elo: {menor_diferenca_elo}")
    
    return melhor_match

def processar_fila():
    """Processa a fila periodicamente para encontrar matches"""
    while True:
        try:
            agora = datetime.now()
            
            # Remove jogadores que esperaram mais de 5 minutos
            for jogador in list(fila.keys()):
                if agora - fila[jogador] > timedelta(minutes=5):
                    del fila[jogador]
                    logger.info(f"Jogador {jogador} removido da fila por timeout")
            
            # Se tiver pelo menos 2 jogadores na fila
            if len(fila) >= 2:
                # Verifica se algum jogador já esperou 30 segundos
                jogador_esperando = None
                for jogador, tempo_entrada in fila.items():
                    if agora - tempo_entrada >= timedelta(seconds=30):
                        jogador_esperando = jogador
                        break
                
                if jogador_esperando:
                    # Tenta encontrar um match para o jogador que esperou 30 segundos
                    jogador2 = encontrar_match(jogador_esperando)
                    
                    if jogador2:
                        # Calcula a diferença de elo
                        elo_j1 = jogadores[jogador_esperando]['elo']
                        elo_j2 = jogadores[jogador2]['elo']
                        diferenca_elo = abs(elo_j1 - elo_j2)
                        
                        # Remove jogadores da fila
                        del fila[jogador_esperando]
                        del fila[jogador2]
                        
                        # Encontra os SIDs dos jogadores
                        sid_j1 = None
                        sid_j2 = None
                        for sid, nickname in sockets_ativos.items():
                            if nickname == jogador_esperando:
                                sid_j1 = sid
                            elif nickname == jogador2:
                                sid_j2 = sid
                        
                        if not sid_j1 or not sid_j2:
                            logger.error(f"Não foi possível encontrar SIDs para os jogadores {jogador_esperando} e {jogador2}")
                            continue
                        
                        # Cria uma nova partida
                        partida = Partida(jogador_esperando, jogador2)
                        
                        # Simula a partida
                        resultado = partida.simular_partida()
                        
                        # Determina o vencedor baseado nas kills
                        vencedor = jogador_esperando if resultado['kills_j1'] > resultado['kills_j2'] else jogador2
                        
                        # Atualiza o elo dos jogadores
                        if vencedor == jogador_esperando:
                            novo_elo_j1, novo_elo_j2 = calcular_novo_elo(elo_j1, elo_j2)
                        else:
                            novo_elo_j2, novo_elo_j1 = calcular_novo_elo(elo_j2, elo_j1)
                        
                        # Atualiza o elo no banco de dados
                        db.atualizar_elo(jogador_esperando, novo_elo_j1)
                        db.atualizar_elo(jogador2, novo_elo_j2)
                        
                        # Atualiza o elo na memória
                        jogadores[jogador_esperando]['elo'] = novo_elo_j1
                        jogadores[jogador2]['elo'] = novo_elo_j2
                        
                        # Salva a partida no banco de dados
                        db.registrar_partida(
                            jogador_esperando,
                            jogador2,
                            vencedor,
                            {
                                'kills_j1': resultado['kills_j1'],
                                'kills_j2': resultado['kills_j2'],
                                'deaths_j1': resultado['deaths_j1'],
                                'deaths_j2': resultado['deaths_j2'],
                                'assists_j1': resultado['assists_j1'],
                                'assists_j2': resultado['assists_j2'],
                                'tempo_partida': resultado['tempo_partida'],
                                'ping': resultado['ping']
                            }
                        )
                        
                        # Notifica os jogadores
                        socketio.emit('match_encontrado', {
                            'jogador2': jogador2,
                            'vencedor': vencedor,
                            'kills_j1': resultado['kills_j1'],
                            'kills_j2': resultado['kills_j2'],
                            'deaths_j1': resultado['deaths_j1'],
                            'deaths_j2': resultado['deaths_j2'],
                            'assists_j1': resultado['assists_j1'],
                            'assists_j2': resultado['assists_j2'],
                            'tempo_partida': resultado['tempo_partida'],
                            'ping': resultado['ping'],
                            'novo_elo': novo_elo_j1
                        }, room=sid_j1)
                        
                        socketio.emit('match_encontrado', {
                            'jogador2': jogador_esperando,
                            'vencedor': vencedor,
                            'kills_j1': resultado['kills_j2'],
                            'kills_j2': resultado['kills_j1'],
                            'deaths_j1': resultado['deaths_j2'],
                            'deaths_j2': resultado['deaths_j1'],
                            'assists_j1': resultado['assists_j2'],
                            'assists_j2': resultado['assists_j1'],
                            'tempo_partida': resultado['tempo_partida'],
                            'ping': resultado['ping'],
                            'novo_elo': novo_elo_j2
                        }, room=sid_j2)
                        
                        logger.info(f"Match encontrado: {jogador_esperando} vs {jogador2}")
                        logger.info(f"Diferença de elo: {diferenca_elo}")
                        logger.info(f"Resultado: {vencedor} venceu com {resultado['kills_j1'] if vencedor == jogador_esperando else resultado['kills_j2']} kills")
            
            time.sleep(0.1)  # Reduzido de 1 segundo para 0.1 segundos
        except Exception as e:
            logger.error(f"Erro ao processar fila: {e}")
            time.sleep(1)  # Mantém 1 segundo em caso de erro

@socketio.on('connect')
def handle_connect():
    logger.info(f"Cliente conectado: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in sockets_ativos:
        nickname = sockets_ativos[request.sid]
        db.sair_da_fila(nickname)
        del sockets_ativos[request.sid]
        leave_room(nickname)
        logger.info(f"Cliente desconectado: {nickname}")

@socketio.on('login')
def handle_login(data):
    try:
        nickname = data['nickname']
        elo = data['elo']
        
        # Verifica se o jogador já existe no banco
        jogador_existente = db.buscar_jogador(nickname)
        if jogador_existente:
            elo = jogador_existente['estatisticas']['elo']
        else:
            # Cria um novo jogador no banco
            db.adicionar_jogador({
                'nickname': nickname,
                'plataforma': 'PC',
                'regiao': 'BR',
                'estatisticas': {
                    'elo': elo,
                    'kills': 0,
                    'deaths': 0,
                    'assists': 0,
                    'vitorias': 0,
                    'derrotas': 0
                },
                'preferences': {}
            })
        
        # Adiciona à lista de jogadores
        jogadores[nickname] = {
            'nickname': nickname,
            'elo': elo
        }
        sockets_ativos[request.sid] = nickname
        
        logger.info(f"Jogador {nickname} fez login com elo {elo}")
        emit('login_sucesso', {
            'nickname': nickname,
            'estatisticas': {
                'elo': elo
            }
        })
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        emit('error', {'message': str(e)})

@socketio.on('entrar_fila')
def handle_entrar_fila():
    try:
        # Verifica se o jogador está logado
        if request.sid not in sockets_ativos:
            return emit('error', {'message': 'Faça login primeiro'})
            
        nickname = sockets_ativos[request.sid]
        
        # Verifica se o jogador existe no banco
        jogador = db.buscar_jogador(nickname)
        if not jogador:
            return emit('error', {'message': 'Jogador não encontrado'})
            
        elo = jogador['estatisticas']['elo']
        
        # Adiciona à fila
        if nickname not in fila:
            fila[nickname] = datetime.now()
            logger.info(f"Jogador {nickname} entrou na fila com elo {elo}")
            emit('fila_entrada', {'message': 'Você entrou na fila'})
            
            # Aguarda 15 segundos antes de procurar match
            time.sleep(15)
            
            # Tenta encontrar um match
            match = encontrar_match(nickname)
            if match:
                # Verifica se o match existe no banco
                jogador_match = db.buscar_jogador(match)
                if not jogador_match:
                    logger.error(f"Jogador {match} não encontrado no banco")
                    return
                    
                elo_match = jogador_match['estatisticas']['elo']
                
                logger.info(f"Match encontrado: {nickname} vs {match}")
                logger.info(f"Elo {nickname}: {elo}")
                logger.info(f"Elo {match}: {elo_match}")
                
                # Remove jogadores da fila
                del fila[nickname]
                del fila[match]
                
                # Cria uma nova partida
                partida = Partida(nickname, match)
                
                # Simula a partida
                resultado = partida.simular_partida()
                
                # Determina o vencedor baseado nas kills
                vencedor = nickname if resultado['kills_j1'] > resultado['kills_j2'] else match
                
                # Atualiza o elo dos jogadores
                if vencedor == nickname:
                    novo_elo_j1, novo_elo_j2 = calcular_novo_elo(elo, elo_match)
                else:
                    novo_elo_j2, novo_elo_j1 = calcular_novo_elo(elo_match, elo)
                
                # Atualiza o elo no banco de dados
                db.atualizar_elo(nickname, novo_elo_j1)
                db.atualizar_elo(match, novo_elo_j2)
                
                # Atualiza o elo na memória
                jogadores[nickname]['elo'] = novo_elo_j1
                jogadores[match]['elo'] = novo_elo_j2
                
                # Salva a partida no banco de dados
                db.registrar_partida(
                    nickname,
                    match,
                    vencedor,
                    {
                        'kills_j1': resultado['kills_j1'],
                        'kills_j2': resultado['kills_j2'],
                        'deaths_j1': resultado['deaths_j1'],
                        'deaths_j2': resultado['deaths_j2'],
                        'assists_j1': resultado['assists_j1'],
                        'assists_j2': resultado['assists_j2'],
                        'tempo_partida': resultado['tempo_partida'],
                        'ping': resultado['ping']
                    }
                )
                
                # Notifica os jogadores
                socketio.emit('match_encontrado', {
                    'jogador2': match,
                    'vencedor': vencedor,
                    'kills_j1': resultado['kills_j1'],
                    'kills_j2': resultado['kills_j2'],
                    'deaths_j1': resultado['deaths_j1'],
                    'deaths_j2': resultado['deaths_j2'],
                    'assists_j1': resultado['assists_j1'],
                    'assists_j2': resultado['assists_j2'],
                    'tempo_partida': resultado['tempo_partida'],
                    'ping': resultado['ping'],
                    'novo_elo': novo_elo_j1
                })
                
                socketio.emit('match_encontrado', {
                    'jogador2': nickname,
                    'vencedor': vencedor,
                    'kills_j1': resultado['kills_j2'],
                    'kills_j2': resultado['kills_j1'],
                    'deaths_j1': resultado['deaths_j2'],
                    'deaths_j2': resultado['deaths_j1'],
                    'assists_j1': resultado['assists_j2'],
                    'assists_j2': resultado['assists_j1'],
                    'tempo_partida': resultado['tempo_partida'],
                    'ping': resultado['ping'],
                    'novo_elo': novo_elo_j2
                })
    except Exception as e:
        logger.error(f"Erro ao entrar na fila: {e}")
        emit('error', {'message': str(e)})

@socketio.on('sair_fila')
def handle_sair_fila():
    try:
        if request.sid not in sockets_ativos:
            return emit('error', {'message': 'Faça login primeiro'})
            
        nickname = sockets_ativos[request.sid]
        if nickname in fila:
            del fila[nickname]
            logger.info(f"Jogador {nickname} saiu da fila")
            emit('fila_saida', {'message': 'Você saiu da fila'})
    except Exception as e:
        logger.error(f"Erro ao sair da fila: {e}")
        emit('error', {'message': str(e)})

@socketio.on('registrar_partida')
def handle_registrar_partida(data):
    try:
        jogador1 = data['jogador1']
        jogador2 = data['jogador2']
        vencedor = data['vencedor']
        
        # Encontra os SIDs dos jogadores
        sid_j1 = list(jogadores.keys())[list(jogadores.values()).index({'nickname': jogador1})]
        sid_j2 = list(jogadores.keys())[list(jogadores.values()).index({'nickname': jogador2})]
        
        # Calcula o novo elo
        elo_j1 = jogadores[sid_j1]['elo']
        elo_j2 = jogadores[sid_j2]['elo']
        
        if vencedor == jogador1:
            novo_elo_j1, novo_elo_j2 = calcular_novo_elo(elo_j1, elo_j2)
        else:
            novo_elo_j2, novo_elo_j1 = calcular_novo_elo(elo_j2, elo_j1)
        
        # Atualiza o elo dos jogadores
        jogadores[sid_j1]['elo'] = novo_elo_j1
        jogadores[sid_j2]['elo'] = novo_elo_j2
        
        # Notifica os jogadores
        emit('partida_registrada', {
            'vencedor': vencedor,
            'novo_mmr_j1': novo_elo_j1
        }, room=sid_j1)
        
        emit('partida_registrada', {
            'vencedor': vencedor,
            'novo_mmr_j1': novo_elo_j2
        }, room=sid_j2)
        
        logger.info(f"Partida registrada: {jogador1} vs {jogador2}, vencedor: {vencedor}")
        logger.info(f"Novo elo {jogador1}: {novo_elo_j1}")
        logger.info(f"Novo elo {jogador2}: {novo_elo_j2}")
    except Exception as e:
        logger.error(f"Erro ao registrar partida: {e}")
        emit('error', {'message': str(e)})

def encerrar_servidor(signum, frame):
    """Função para encerrar o servidor de forma limpa"""
    logger.info("Encerrando servidor...")
    sys.exit(0)

if __name__ == '__main__':
    try:
        logger.info("Iniciando servidor de matchmaking...")
        
        # Configura o handler para SIGINT (Ctrl+C)
        signal.signal(signal.SIGINT, encerrar_servidor)
        
        # Inicia o processamento da fila em uma thread separada
        thread_fila = threading.Thread(target=processar_fila)
        thread_fila.daemon = True
        thread_fila.start()
        
        # Inicia o servidor com threading
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("Servidor encerrado pelo usuário")
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")
    finally:
        logger.info("Servidor encerrado") 