import sqlite3
from typing import List, Dict, Optional
import json
from datetime import datetime
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name: str = "matchmaking.db"):
        self.conn = sqlite3.connect(db_name)
        self.criar_tabelas()

    def criar_tabelas(self):
        cursor = self.conn.cursor()
        
        # Tabela de jogadores
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS jogadores (
            nickname TEXT PRIMARY KEY,
            plataforma TEXT NOT NULL,
            regiao TEXT NOT NULL,
            estatisticas TEXT NOT NULL,
            preferences TEXT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultimo_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            em_fila BOOLEAN DEFAULT FALSE
        )
        ''')
        
        # Tabela de partidas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS partidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jogador1 TEXT NOT NULL,
            jogador2 TEXT NOT NULL,
            vencedor TEXT NOT NULL,
            dados_partida TEXT NOT NULL,
            data_partida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (jogador1) REFERENCES jogadores(nickname),
            FOREIGN KEY (jogador2) REFERENCES jogadores(nickname)
        )
        ''')
        
        self.conn.commit()
        logger.info("Tabelas criadas com sucesso")

    def adicionar_jogador(self, jogador: Dict):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO jogadores (nickname, plataforma, regiao, estatisticas, preferences)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                jogador['nickname'],
                jogador['plataforma'],
                jogador['regiao'],
                json.dumps(jogador['estatisticas']),
                json.dumps(jogador['preferences'])
            ))
            self.conn.commit()
            logger.info(f"Jogador {jogador['nickname']} adicionado com sucesso")
        except sqlite3.IntegrityError:
            logger.warning(f"Jogador {jogador['nickname']} já existe no banco")
        except Exception as e:
            logger.error(f"Erro ao adicionar jogador {jogador['nickname']}: {e}")

    def atualizar_elo(self, nickname: str, novo_elo: int):
        cursor = self.conn.cursor()
        try:
            # Busca o jogador
            cursor.execute('SELECT estatisticas FROM jogadores WHERE nickname = ?', (nickname,))
            row = cursor.fetchone()
            if not row:
                logger.error(f"Jogador {nickname} não encontrado para atualização de elo")
                return
                
            # Atualiza o elo nas estatísticas
            estatisticas = json.loads(row[0])
            estatisticas['elo'] = novo_elo
            
            # Atualiza no banco
            cursor.execute('''
            UPDATE jogadores
            SET estatisticas = ?
            WHERE nickname = ?
            ''', (json.dumps(estatisticas), nickname))
            
            self.conn.commit()
            logger.info(f"Elo do jogador {nickname} atualizado para {novo_elo}")
        except Exception as e:
            logger.error(f"Erro ao atualizar elo do jogador {nickname}: {e}")

    def atualizar_jogador(self, jogador: Dict):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE jogadores
        SET estatisticas = ?, preferences = ?, ultimo_login = CURRENT_TIMESTAMP
        WHERE nickname = ?
        ''', (
            json.dumps(jogador['estatisticas']),
            json.dumps(jogador['preferences']),
            jogador['nickname']
        ))
        self.conn.commit()

    def buscar_jogador(self, nickname: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        try:
            cursor.execute('SELECT * FROM jogadores WHERE nickname = ?', (nickname,))
            row = cursor.fetchone()
            
            if row:
                logger.info(f"Jogador {nickname} encontrado no banco")
                return {
                    'nickname': row[0],
                    'plataforma': row[1],
                    'regiao': row[2],
                    'estatisticas': json.loads(row[3]),
                    'preferences': json.loads(row[4]),
                    'data_criacao': row[5],
                    'ultimo_login': row[6],
                    'em_fila': bool(row[7])
                }
            logger.warning(f"Jogador {nickname} não encontrado no banco")
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar jogador {nickname}: {e}")
            return None

    def buscar_jogadores_em_fila(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM jogadores WHERE em_fila = TRUE')
        rows = cursor.fetchall()
        
        jogadores = []
        for row in rows:
            jogadores.append({
                'nickname': row[0],
                'plataforma': row[1],
                'regiao': row[2],
                'estatisticas': json.loads(row[3]),
                'preferences': json.loads(row[4]),
                'data_criacao': row[5],
                'ultimo_login': row[6],
                'em_fila': bool(row[7])
            })
        return jogadores

    def entrar_na_fila(self, nickname: str):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE jogadores
        SET em_fila = TRUE, ultimo_login = CURRENT_TIMESTAMP
        WHERE nickname = ?
        ''', (nickname,))
        self.conn.commit()

    def sair_da_fila(self, nickname: str):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE jogadores
        SET em_fila = FALSE
        WHERE nickname = ?
        ''', (nickname,))
        self.conn.commit()

    def registrar_partida(self, jogador1: str, jogador2: str, vencedor: str, dados_partida: Dict):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO partidas (jogador1, jogador2, vencedor, dados_partida)
        VALUES (?, ?, ?, ?)
        ''', (
            jogador1,
            jogador2,
            vencedor,
            json.dumps(dados_partida)
        ))
        self.conn.commit()

    def buscar_historico_partidas(self, nickname: str, limite: int = 10) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT * FROM partidas
        WHERE jogador1 = ? OR jogador2 = ?
        ORDER BY data_partida DESC
        LIMIT ?
        ''', (nickname, nickname, limite))
        rows = cursor.fetchall()
        
        partidas = []
        for row in rows:
            partidas.append({
                'id': row[0],
                'jogador1': row[1],
                'jogador2': row[2],
                'vencedor': row[3],
                'dados_partida': json.loads(row[4]),
                'data_partida': row[5]
            })
        return partidas

    def fechar(self):
        self.conn.close() 