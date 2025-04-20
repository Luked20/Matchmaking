from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
import random
from enum import Enum
import numpy as np
from dataclasses import field
from ia_matchmaking import SistemaIA

class Plataforma(Enum):
    PC = "PC"
    PS4 = "PS4"
    XBOX = "XBOX"
    MOBILE = "MOBILE"

class Regiao(Enum):
    BR = "Brasil"
    NA = "América do Norte"
    EU = "Europa"
    AS = "Ásia"

class EstiloJogo(Enum):
    AGRESSIVO = "Agressivo"
    DEFENSIVO = "Defensivo"
    SUPORTE = "Suporte"
    HÍBRIDO = "Híbrido"

class Comportamento(Enum):
    EXCELENTE = 5
    BOM = 4
    REGULAR = 3
    RUIM = 2
    PÉSSIMO = 1

@dataclass
class Estatisticas:
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    vitorias: int = 0
    derrotas: int = 0
    tempo_total_jogo: int = 0
    partidas_jogadas: int = 0
    abandonos: int = 0
    reports: int = 0
    ping_medio: float = 0.0
    estilo_jogo: EstiloJogo = EstiloJogo.HÍBRIDO
    comportamento: Comportamento = Comportamento.REGULAR
    mmr: float = 1000.0  # Match Making Rating
    mmr_historico: List[float] = field(default_factory=list)

    @property
    def kd_ratio(self) -> float:
        return self.kills / self.deaths if self.deaths > 0 else self.kills

    @property
    def win_rate(self) -> float:
        return (self.vitorias / self.partidas_jogadas * 100) if self.partidas_jogadas > 0 else 0

    @property
    def tempo_medio_partida(self) -> float:
        return self.tempo_total_jogo / self.partidas_jogadas if self.partidas_jogadas > 0 else 0

    @property
    def taxa_abandono(self) -> float:
        return (self.abandonos / self.partidas_jogadas * 100) if self.partidas_jogadas > 0 else 0

    def atualizar_mmr(self, resultado: bool, mmr_oponente: float, k: float = 32):
        expected = 1 / (1 + 10 ** ((mmr_oponente - self.mmr) / 400))
        actual = 1 if resultado else 0
        
        # Ajusta o K baseado no comportamento
        k_ajustado = k * (self.comportamento.value / 5)
        
        # Atualiza o MMR
        self.mmr += k_ajustado * (actual - expected)
        self.mmr_historico.append(self.mmr)

class Jogador:
    def __init__(self, nickname: str, plataforma: Plataforma, regiao: Regiao):
        self.nickname = nickname
        self.plataforma = plataforma
        self.regiao = regiao
        self.estatisticas = Estatisticas()
        self.historico_partidas: List[Dict] = []
        self.preferences = {
            'modo_preferido': None,
            'horario_preferido': None,
            'idioma': 'pt-BR'
        }
        self.sistema_ia = SistemaIA()

    def adicionar_partida(self, vitoria: bool, kills: int, deaths: int, assists: int, 
                         tempo_partida: int, ping: float, abandonou: bool = False, 
                         comportamento: Comportamento = Comportamento.REGULAR):
        try:
            self.estatisticas.kills += kills
            self.estatisticas.deaths += deaths
            self.estatisticas.assists += assists
            self.estatisticas.tempo_total_jogo += tempo_partida
            self.estatisticas.partidas_jogadas += 1
            self.estatisticas.ping_medio = (self.estatisticas.ping_medio * (self.estatisticas.partidas_jogadas - 1) + ping) / self.estatisticas.partidas_jogadas
            
            if abandonou:
                self.estatisticas.abandonos += 1
                self.estatisticas.comportamento = max(Comportamento.PÉSSIMO, 
                                                    Comportamento(self.estatisticas.comportamento.value - 1))
            
            if vitoria:
                self.estatisticas.vitorias += 1
            else:
                self.estatisticas.derrotas += 1
            
            # Atualiza comportamento
            if comportamento.value < self.estatisticas.comportamento.value:
                self.estatisticas.comportamento = comportamento
                
            # Atualiza MMR usando o sistema de IA
            dados_jogador = self.to_dict()
            novo_mmr = self.sistema_ia.predizer_performance(dados_jogador)
            self.estatisticas.mmr = novo_mmr
            
            # Adiciona ao histórico de MMR
            self.estatisticas.mmr_historico.append(novo_mmr)

            self.historico_partidas.append({
                'data': datetime.now().isoformat(),
                'resultado': 'Vitória' if vitoria else 'Derrota',
                'kills': kills,
                'deaths': deaths,
                'assists': assists,
                'tempo_partida': tempo_partida,
                'ping': ping,
                'abandonou': abandonou
            })
        except Exception as e:
            print(f"Erro ao adicionar partida: {e}")

    def to_dict(self) -> Dict:
        return {
            'nickname': self.nickname,
            'plataforma': self.plataforma.value,
            'regiao': self.regiao.value,
            'estatisticas': {
                'kills': self.estatisticas.kills,
                'deaths': self.estatisticas.deaths,
                'assists': self.estatisticas.assists,
                'vitorias': self.estatisticas.vitorias,
                'derrotas': self.estatisticas.derrotas,
                'tempo_total_jogo': self.estatisticas.tempo_total_jogo,
                'partidas_jogadas': self.estatisticas.partidas_jogadas,
                'abandonos': self.estatisticas.abandonos,
                'reports': self.estatisticas.reports,
                'ping_medio': self.estatisticas.ping_medio,
                'estilo_jogo': self.estatisticas.estilo_jogo.value,
                'comportamento': self.estatisticas.comportamento.value,
                'mmr': self.estatisticas.mmr,
                'mmr_historico': self.estatisticas.mmr_historico
            },
            'preferences': self.preferences
        }

class SistemaMatchmaking:
    def __init__(self):
        self.jogadores: Dict[str, Jogador] = {}
        self.partidas_em_andamento: List[Dict] = []
        self.sistema_ia = SistemaIA()

    def cadastrar_jogador(self, nickname: str, plataforma: Plataforma, regiao: Regiao) -> Jogador:
        if nickname in self.jogadores:
            raise ValueError("Nickname já está em uso")
        
        jogador = Jogador(nickname, plataforma, regiao)
        self.jogadores[nickname] = jogador
        
        # Verifica se é possível smurf
        dados_jogador = jogador.to_dict()
        eh_smurf, prob_smurf = self.sistema_ia.detectar_smurf(dados_jogador)
        if eh_smurf:
            print(f"Alerta: Jogador {nickname} pode ser smurf (probabilidade: {prob_smurf:.2f})")
            
        return jogador

    def encontrar_jogadores_compatíveis(self, jogador: Jogador, 
                                     diferenca_mmr_max: int = 200,
                                     regiao_preferida: bool = True) -> List[Tuple[Jogador, float]]:
        try:
            # Usa o sistema de IA para recomendar teammates
            dados_jogador = jogador.to_dict()
            todos_jogadores = [j.to_dict() for j in self.jogadores.values()]
            
            recomendacoes = self.sistema_ia.recomendar_teammates(
                dados_jogador, 
                todos_jogadores,
                n_recomendacoes=10
            )
            
            # Converte de volta para objetos Jogador
            jogadores_compatíveis = []
            for rec in recomendacoes:
                jogador_rec = self.jogadores[rec['nickname']]
                score = self.sistema_ia.calcular_score_compatibilidade(
                    dados_jogador,
                    rec
                )
                jogadores_compatíveis.append((jogador_rec, score))
                
            return jogadores_compatíveis
        except Exception as e:
            print(f"Erro ao encontrar jogadores compatíveis: {e}")
            return []

    def simular_partida(self, jogador1: Jogador, jogador2: Jogador) -> Dict:
        try:
            # Prediz performance dos jogadores
            dados_j1 = jogador1.to_dict()
            dados_j2 = jogador2.to_dict()
            
            pred_perf_j1 = self.sistema_ia.predizer_performance(dados_j1)
            pred_perf_j2 = self.sistema_ia.predizer_performance(dados_j2)
            
            # Ajusta probabilidade de vitória baseado na predição
            prob_base = 1 / (1 + 10 ** ((jogador2.estatisticas.mmr - jogador1.estatisticas.mmr) / 400))
            prob_ajustada = prob_base * (pred_perf_j1 / (pred_perf_j1 + pred_perf_j2))
            
            vitoria_j1 = random.random() < prob_ajustada
            
            # Gera estatísticas aleatórias para a partida
            kills_j1 = random.randint(0, 20)
            deaths_j1 = random.randint(0, 10)
            assists_j1 = random.randint(0, 15)
            tempo_partida = random.randint(10, 30)
            ping = random.uniform(20, 100)
            
            # Chance de abandono baseada no comportamento e toxicidade
            eh_toxico_j1, prob_tox_j1 = self.sistema_ia.detectar_toxicidade(dados_j1)
            abandonou = random.random() < (0.1 * (6 - jogador1.estatisticas.comportamento.value) * 
                                         (1 + prob_tox_j1))
            
            # Atualiza os jogadores
            jogador1.adicionar_partida(vitoria_j1, kills_j1, deaths_j1, assists_j1, 
                                     tempo_partida, ping, abandonou)
            jogador2.adicionar_partida(not vitoria_j1, deaths_j1, kills_j1, assists_j1, 
                                     tempo_partida, ping)
            
            # Atualiza o MMR
            jogador1.estatisticas.atualizar_mmr(vitoria_j1, jogador2.estatisticas.mmr)
            jogador2.estatisticas.atualizar_mmr(not vitoria_j1, jogador1.estatisticas.mmr)
            
            # Treina o modelo com os novos dados
            if len(self.jogadores) >= 10:
                dados_treinamento = [j.to_dict() for j in self.jogadores.values()]
                self.sistema_ia.treinar_modelo_performance(dados_treinamento)
            
            return {
                'jogador1': jogador1.nickname,
                'jogador2': jogador2.nickname,
                'vencedor': jogador1.nickname if vitoria_j1 else jogador2.nickname,
                'kills_j1': kills_j1,
                'deaths_j1': deaths_j1,
                'assists_j1': assists_j1,
                'tempo_partida': tempo_partida,
                'ping': ping,
                'abandonou': abandonou,
                'predicao_performance_j1': pred_perf_j1,
                'predicao_performance_j2': pred_perf_j2
            }
        except Exception as e:
            print(f"Erro ao simular partida: {e}")
            return {}

    def salvar_estado(self, arquivo: str):
        try:
            estado = {
                'jogadores': {nick: jogador.to_dict() for nick, jogador in self.jogadores.items()}
            }
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(estado, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar estado: {e}")

    def carregar_estado(self, arquivo: str):
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                estado = json.load(f)
            
            self.jogadores = {}
            for nick, dados in estado['jogadores'].items():
                jogador = Jogador(
                    nick,
                    Plataforma(dados['plataforma']),
                    Regiao(dados['regiao'])
                )
                jogador.estatisticas = Estatisticas(**dados['estatisticas'])
                jogador.preferences = dados['preferences']
                self.jogadores[nick] = jogador
        except Exception as e:
            print(f"Erro ao carregar estado: {e}")

class Partida:
    def __init__(self, jogador1: str, jogador2: str):
        self.jogador1 = jogador1
        self.jogador2 = jogador2
        self.kills_j1 = 0
        self.kills_j2 = 0
        self.deaths_j1 = 0
        self.deaths_j2 = 0
        self.assists_j1 = 0
        self.assists_j2 = 0
        self.tempo_partida = 0
        self.ping = 0
    
    def simular_partida(self):
        """Simula uma partida com resultados aleatórios"""
        # Gera estatísticas aleatórias para o jogador 1
        self.kills_j1 = random.randint(0, 20)
        self.deaths_j1 = random.randint(0, 10)
        self.assists_j1 = random.randint(0, 15)
        
        # Gera estatísticas aleatórias para o jogador 2
        self.kills_j2 = random.randint(0, 20)
        self.deaths_j2 = random.randint(0, 10)
        self.assists_j2 = random.randint(0, 15)
        
        # Gera outros dados da partida
        self.tempo_partida = random.randint(10, 30)
        self.ping = random.uniform(20, 100)
        
        return {
            'kills_j1': self.kills_j1,
            'kills_j2': self.kills_j2,
            'deaths_j1': self.deaths_j1,
            'deaths_j2': self.deaths_j2,
            'assists_j1': self.assists_j1,
            'assists_j2': self.assists_j2,
            'tempo_partida': self.tempo_partida,
            'ping': self.ping
        }

def main():
    try:
        # Exemplo de uso
        sistema = SistemaMatchmaking()
        
        # Cadastra alguns jogadores com diferentes estilos
        jogadores = [
            sistema.cadastrar_jogador("Player1", Plataforma.PC, Regiao.BR),
            sistema.cadastrar_jogador("Player2", Plataforma.PS4, Regiao.BR),
            sistema.cadastrar_jogador("Player3", Plataforma.XBOX, Regiao.NA),
            sistema.cadastrar_jogador("Player4", Plataforma.MOBILE, Regiao.EU)
        ]
        
        # Define estilos de jogo
        jogadores[0].estatisticas.estilo_jogo = EstiloJogo.AGRESSIVO
        jogadores[1].estatisticas.estilo_jogo = EstiloJogo.SUPORTE
        jogadores[2].estatisticas.estilo_jogo = EstiloJogo.DEFENSIVO
        jogadores[3].estatisticas.estilo_jogo = EstiloJogo.HÍBRIDO
        
        # Simula algumas partidas
        for _ in range(10):
            for jogador in jogadores:
                compatíveis = sistema.encontrar_jogadores_compatíveis(jogador)
                if compatíveis:
                    oponente, score = compatíveis[0]
                    resultado = sistema.simular_partida(jogador, oponente)
                    print(f"\nPartida entre {jogador.nickname} e {oponente.nickname}:")
                    print(f"Score de compatibilidade: {score:.2f}")
                    print(f"Predição de performance: {resultado['predicao_performance_j1']:.2f} vs {resultado['predicao_performance_j2']:.2f}")
                    print(f"Vencedor: {resultado['vencedor']}")
                    print(f"K/D/A: {resultado['kills_j1']}/{resultado['deaths_j1']}/{resultado['assists_j1']}")
                    print(f"Ping: {resultado['ping']:.1f}ms")
                    if resultado['abandonou']:
                        print("Jogador abandonou a partida!")
        
        # Mostra estatísticas finais
        print("\n=== ESTATÍSTICAS FINAIS ===")
        for jogador in sorted(jogadores, key=lambda x: x.estatisticas.mmr, reverse=True):
            print(f"\n{jogador.nickname}:")
            print(f"MMR: {jogador.estatisticas.mmr:.2f}")
            print(f"K/D Ratio: {jogador.estatisticas.kd_ratio:.2f}")
            print(f"Win Rate: {jogador.estatisticas.win_rate:.1f}%")
            print(f"Ping médio: {jogador.estatisticas.ping_medio:.1f}ms")
            print(f"Estilo de jogo: {jogador.estatisticas.estilo_jogo.value}")
            print(f"Comportamento: {jogador.estatisticas.comportamento.value}")
            print(f"Taxa de abandono: {jogador.estatisticas.taxa_abandono:.1f}%")
            
            # Verifica se é smurf ou tóxico
            dados_jogador = jogador.to_dict()
            eh_smurf, prob_smurf = sistema.sistema_ia.detectar_smurf(dados_jogador)
            eh_toxico, prob_tox = sistema.sistema_ia.detectar_toxicidade(dados_jogador)
            
            if eh_smurf:
                print(f"⚠️ Possível smurf (probabilidade: {prob_smurf:.2f})")
            if eh_toxico:
                print(f"⚠️ Comportamento tóxico detectado (probabilidade: {prob_tox:.2f})")
    except Exception as e:
        print(f"Erro na execução do programa: {e}")

if __name__ == "__main__":
    main() 