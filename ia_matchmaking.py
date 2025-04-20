import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from typing import List, Dict, Tuple
import joblib
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class SistemaIA:
    def __init__(self):
        self.modelo_performance = None
        self.modelo_clustering = None
        self.scaler = StandardScaler()
        self.modelo_treinado = False
        self.carregar_modelos()
        self.treinar_com_dados_iniciais()

    def carregar_modelos(self):
        try:
            if os.path.exists('modelo_performance.pkl'):
                self.modelo_performance = joblib.load('modelo_performance.pkl')
                self.modelo_treinado = True
            else:
                self.modelo_performance = RandomForestRegressor(n_estimators=100, random_state=42)
                self.modelo_treinado = False

            if os.path.exists('modelo_clustering.pkl'):
                self.modelo_clustering = joblib.load('modelo_clustering.pkl')
            else:
                self.modelo_clustering = KMeans(n_clusters=3, random_state=42)
                
            if os.path.exists('scaler.pkl'):
                self.scaler = joblib.load('scaler.pkl')
            else:
                self.scaler = StandardScaler()
        except Exception as e:
            print(f"Erro ao carregar modelos: {e}")
            self.modelo_performance = RandomForestRegressor(n_estimators=100, random_state=42)
            self.modelo_clustering = KMeans(n_clusters=3, random_state=42)
            self.scaler = StandardScaler()
            self.modelo_treinado = False

    def treinar_com_dados_iniciais(self):
        """Treina o modelo com dados iniciais para evitar erros de predição"""
        if self.modelo_treinado:
            return

        dados_iniciais = [
            {
                'estatisticas': {
                    'mmr': 1000,
                    'kills': 10,
                    'deaths': 5,
                    'vitorias': 5,
                    'partidas_jogadas': 10,
                    'ping_medio': 50,
                    'comportamento': 3,
                    'abandonos': 0,
                    'reports': 0
                }
            },
            {
                'estatisticas': {
                    'mmr': 1500,
                    'kills': 15,
                    'deaths': 3,
                    'vitorias': 8,
                    'partidas_jogadas': 10,
                    'ping_medio': 40,
                    'comportamento': 4,
                    'abandonos': 0,
                    'reports': 0
                }
            },
            {
                'estatisticas': {
                    'mmr': 2000,
                    'kills': 20,
                    'deaths': 2,
                    'vitorias': 9,
                    'partidas_jogadas': 10,
                    'ping_medio': 30,
                    'comportamento': 5,
                    'abandonos': 0,
                    'reports': 0
                }
            }
        ]
        
        try:
            self.treinar_modelo_performance(dados_iniciais)
            self.modelo_treinado = True
        except Exception as e:
            print(f"Erro ao treinar com dados iniciais: {e}")

    def salvar_modelos(self):
        try:
            joblib.dump(self.modelo_performance, 'modelo_performance.pkl')
            joblib.dump(self.modelo_clustering, 'modelo_clustering.pkl')
            joblib.dump(self.scaler, 'scaler.pkl')
        except Exception as e:
            print(f"Erro ao salvar modelos: {e}")

    def calcular_metricas(self, jogador: Dict) -> Tuple[float, float]:
        """Calcula kd_ratio e win_rate de forma segura"""
        try:
            deaths = max(1, jogador['estatisticas']['deaths'])
            kd_ratio = jogador['estatisticas']['kills'] / deaths
            
            partidas = max(1, jogador['estatisticas']['partidas_jogadas'])
            win_rate = jogador['estatisticas']['vitorias'] / partidas * 100
            
            return kd_ratio, win_rate
        except Exception as e:
            print(f"Erro ao calcular métricas: {e}")
            return 1.0, 50.0  # Valores padrão seguros

    def preparar_dados_treinamento(self, jogadores: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        if not jogadores:
            return np.array([]), np.array([])
            
        X = []
        y = []
        
        for jogador in jogadores:
            try:
                kd_ratio, win_rate = self.calcular_metricas(jogador)
                
                features = [
                    jogador['estatisticas']['mmr'],
                    kd_ratio,
                    win_rate,
                    jogador['estatisticas']['ping_medio'],
                    jogador['estatisticas']['comportamento']
                ]
                X.append(features)
                y.append(jogador['estatisticas']['mmr'])
            except Exception as e:
                print(f"Erro ao preparar dados de treinamento: {e}")
                continue
            
        return np.array(X), np.array(y)

    def treinar_modelo_performance(self, dados_treinamento: List[Dict]):
        if not dados_treinamento:
            return
            
        try:
            X, y = self.preparar_dados_treinamento(dados_treinamento)
            if len(X) == 0:
                return
                
            X_scaled = self.scaler.fit_transform(X)
            self.modelo_performance.fit(X_scaled, y)
            self.modelo_treinado = True
            self.salvar_modelos()
        except Exception as e:
            print(f"Erro ao treinar modelo: {e}")

    def predizer_performance(self, jogador: Dict) -> float:
        if not jogador or 'estatisticas' not in jogador:
            return 1000.0  # Valor padrão seguro
            
        try:
            if not self.modelo_treinado:
                return jogador['estatisticas']['mmr']  # Retorna MMR atual se modelo não treinado
                
            kd_ratio, win_rate = self.calcular_metricas(jogador)
            
            features = np.array([
                jogador['estatisticas']['mmr'],
                kd_ratio,
                win_rate,
                jogador['estatisticas']['ping_medio'],
                jogador['estatisticas']['comportamento']
            ]).reshape(1, -1)
            
            # Garante que o scaler está treinado
            if not hasattr(self.scaler, 'mean_'):
                X, _ = self.preparar_dados_treinamento([jogador])
                if len(X) > 0:
                    self.scaler.fit(X)
            
            features_scaled = self.scaler.transform(features)
            return self.modelo_performance.predict(features_scaled)[0]
        except Exception as e:
            print(f"Erro ao prever performance: {e}")
            return jogador['estatisticas']['mmr']  # Retorna MMR atual em caso de erro

    def detectar_smurf(self, jogador: Dict) -> Tuple[bool, float]:
        if not jogador or 'estatisticas' not in jogador:
            return False, 0.0
            
        try:
            padroes_suspeitos = 0
            kd_ratio, win_rate = self.calcular_metricas(jogador)
            
            # 1. Win rate muito alta
            if win_rate > 80:
                padroes_suspeitos += 1
                
            # 2. K/D ratio muito alto
            if kd_ratio > 5:
                padroes_suspeitos += 1
                
            # 3. MMR subindo muito rápido
            if 'mmr_historico' in jogador['estatisticas'] and len(jogador['estatisticas']['mmr_historico']) > 10:
                mmr_inicial = jogador['estatisticas']['mmr_historico'][0]
                mmr_atual = jogador['estatisticas']['mmr']
                if (mmr_atual - mmr_inicial) > 500:
                    padroes_suspeitos += 1
                    
            # 4. Poucas partidas jogadas
            if jogador['estatisticas']['partidas_jogadas'] < 20:
                padroes_suspeitos += 1
                
            probabilidade_smurf = padroes_suspeitos / 4
            return probabilidade_smurf > 0.5, probabilidade_smurf
        except Exception as e:
            print(f"Erro ao detectar smurf: {e}")
            return False, 0.0

    def detectar_toxicidade(self, jogador: Dict) -> Tuple[bool, float]:
        if not jogador or 'estatisticas' not in jogador:
            return False, 0.0
            
        try:
            padroes_toxicos = 0
            
            # 1. Alta taxa de abandono
            if jogador['estatisticas']['abandonos'] / max(1, jogador['estatisticas']['partidas_jogadas']) * 100 > 20:
                padroes_toxicos += 1
                
            # 2. Muitos reports
            if jogador['estatisticas']['reports'] > 5:
                padroes_toxicos += 1
                
            # 3. Comportamento ruim
            if jogador['estatisticas']['comportamento'] < 3:
                padroes_toxicos += 1
                
            probabilidade_toxicidade = padroes_toxicos / 3
            return probabilidade_toxicidade > 0.5, probabilidade_toxicidade
        except Exception as e:
            print(f"Erro ao detectar toxicidade: {e}")
            return False, 0.0

    def agrupar_jogadores(self, jogadores: List[Dict]) -> Dict[int, List[Dict]]:
        if not jogadores:
            return {}
            
        try:
            # Prepara dados para clustering
            X = []
            for jogador in jogadores:
                kd_ratio, win_rate = self.calcular_metricas(jogador)
                
                features = [
                    jogador['estatisticas']['mmr'],
                    kd_ratio,
                    win_rate,
                    jogador['estatisticas']['ping_medio'],
                    jogador['estatisticas']['comportamento']
                ]
                X.append(features)
                
            X = np.array(X)
            
            # Ajusta número de clusters baseado no número de amostras únicas
            X_unique = np.unique(X, axis=0)
            n_clusters = min(3, len(X_unique))
            if n_clusters < 2:
                return {0: jogadores}
                
            self.modelo_clustering.n_clusters = n_clusters
            X_scaled = self.scaler.fit_transform(X)
            
            # Aplica clustering
            clusters = self.modelo_clustering.fit_predict(X_scaled)
            
            # Agrupa jogadores por cluster
            grupos = {}
            for i, cluster in enumerate(clusters):
                if cluster not in grupos:
                    grupos[cluster] = []
                grupos[cluster].append(jogadores[i])
                
            return grupos
        except Exception as e:
            print(f"Erro ao agrupar jogadores: {e}")
            return {0: jogadores}  # Retorna todos em um grupo em caso de erro

    def recomendar_teammates(self, jogador: Dict, todos_jogadores: List[Dict], 
                           n_recomendacoes: int = 5) -> List[Dict]:
        if not jogador or not todos_jogadores:
            return []
            
        try:
            # Agrupa jogadores
            grupos = self.agrupar_jogadores(todos_jogadores)
            
            # Encontra o cluster do jogador
            cluster_jogador = None
            for cluster, membros in grupos.items():
                if any(m['nickname'] == jogador['nickname'] for m in membros):
                    cluster_jogador = cluster
                    break
                    
            if cluster_jogador is None:
                return []
                
            # Filtra recomendações
            recomendacoes = []
            for membro in grupos[cluster_jogador]:
                if membro['nickname'] != jogador['nickname']:
                    score = self.calcular_score_compatibilidade(jogador, membro)
                    recomendacoes.append((membro, score))
                    
            # Ordena por score e retorna os melhores
            recomendacoes.sort(key=lambda x: x[1], reverse=True)
            return [r[0] for r in recomendacoes[:n_recomendacoes]]
        except Exception as e:
            print(f"Erro ao recomendar teammates: {e}")
            return []

    def calcular_score_compatibilidade(self, jogador1: Dict, jogador2: Dict) -> float:
        if not jogador1 or not jogador2:
            return 0.0
            
        try:
            scores = []
            
            # 1. Diferença de MMR
            diff_mmr = abs(jogador1['estatisticas']['mmr'] - jogador2['estatisticas']['mmr'])
            score_mmr = max(0, 1 - (diff_mmr / 500))
            
            # 2. Compatibilidade de região
            if jogador1['regiao'] == jogador2['regiao']:
                score_regiao = 1.0
            else:
                score_regiao = 0.5
                
            # 3. Compatibilidade de estilo
            if jogador1['estatisticas']['estilo_jogo'] == jogador2['estatisticas']['estilo_jogo']:
                score_estilo = 1.0
            else:
                score_estilo = 0.7
                
            # 4. Comportamento
            score_comportamento = (jogador1['estatisticas']['comportamento'] + 
                                 jogador2['estatisticas']['comportamento']) / 10
            
            # Combina scores
            scores = [score_mmr, score_regiao, score_estilo, score_comportamento]
            pesos = [0.4, 0.3, 0.2, 0.1]
            
            return sum(s * p for s, p in zip(scores, pesos))
        except Exception as e:
            print(f"Erro ao calcular score de compatibilidade: {e}")
            return 0.5  # Score médio em caso de erro 