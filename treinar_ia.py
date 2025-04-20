from ia_matchmaking import SistemaIA
import numpy as np
import os
from typing import List, Dict

def criar_dados_treinamento() -> List[Dict]:
    """Cria dados de exemplo para treinamento"""
    dados = []
    
    # Jogadores iniciantes (100)
    print("Gerando jogadores iniciantes...")
    for i in range(100):
        dados.append({
            'nickname': f'Iniciante_{i+1}',
            'regiao': 'BR',
            'estatisticas': {
                'mmr': np.random.randint(800, 1200),
                'kills': np.random.randint(5, 15),
                'deaths': np.random.randint(8, 20),
                'vitorias': np.random.randint(2, 8),
                'partidas_jogadas': np.random.randint(10, 30),
                'ping_medio': np.random.randint(30, 100),
                'comportamento': np.random.randint(3, 5),
                'abandonos': np.random.randint(0, 2),
                'reports': np.random.randint(0, 2),
                'estilo_jogo': np.random.choice(['Agressivo', 'Defensivo', 'Equilibrado']),
                'mmr_historico': [np.random.randint(800, 1200) for _ in range(5)]
            }
        })
    
    # Jogadores intermediários (100)
    print("Gerando jogadores intermediários...")
    for i in range(100):
        dados.append({
            'nickname': f'Intermediario_{i+1}',
            'regiao': 'BR',
            'estatisticas': {
                'mmr': np.random.randint(1200, 1800),
                'kills': np.random.randint(10, 20),
                'deaths': np.random.randint(5, 15),
                'vitorias': np.random.randint(5, 12),
                'partidas_jogadas': np.random.randint(30, 100),
                'ping_medio': np.random.randint(20, 80),
                'comportamento': np.random.randint(4, 6),
                'abandonos': np.random.randint(0, 1),
                'reports': np.random.randint(0, 1),
                'estilo_jogo': np.random.choice(['Agressivo', 'Defensivo', 'Equilibrado']),
                'mmr_historico': [np.random.randint(1200, 1800) for _ in range(10)]
            }
        })
    
    # Jogadores avançados (100)
    print("Gerando jogadores avançados...")
    for i in range(100):
        dados.append({
            'nickname': f'Avancado_{i+1}',
            'regiao': 'BR',
            'estatisticas': {
                'mmr': np.random.randint(1800, 2500),
                'kills': np.random.randint(15, 25),
                'deaths': np.random.randint(3, 10),
                'vitorias': np.random.randint(8, 15),
                'partidas_jogadas': np.random.randint(100, 300),
                'ping_medio': np.random.randint(10, 50),
                'comportamento': np.random.randint(5, 7),
                'abandonos': 0,
                'reports': 0,
                'estilo_jogo': np.random.choice(['Agressivo', 'Defensivo', 'Equilibrado']),
                'mmr_historico': [np.random.randint(1800, 2500) for _ in range(15)]
            }
        })
    
    return dados

def main():
    print("Inicializando sistema de matchmaking...")
    
    # Remove arquivos de modelo antigos se existirem
    if os.path.exists('modelo_performance.pkl'):
        os.remove('modelo_performance.pkl')
    if os.path.exists('modelo_clustering.pkl'):
        os.remove('modelo_clustering.pkl')
    
    # Inicializa o sistema
    sistema = SistemaIA()
    
    # Cria dados de treinamento
    print("\nCriando dados de treinamento...")
    dados_treinamento = criar_dados_treinamento()
    print(f"Total de jogadores gerados: {len(dados_treinamento)}")
    
    # Treina o modelo
    print("\nTreinando modelo...")
    sistema.treinar_modelo_performance(dados_treinamento)
    
    # Testa o modelo
    print("\nTestando modelo com alguns exemplos:")
    for i, jogador in enumerate(dados_treinamento[:100]):
        mmr_predito = sistema.predizer_performance(jogador)
        print(f"\nJogador {jogador['nickname']}:")
        print(f"  MMR Real: {jogador['estatisticas']['mmr']}")
        print(f"  MMR Predito: {mmr_predito:.2f}")
        print(f"  Diferença: {abs(jogador['estatisticas']['mmr'] - mmr_predito):.2f}")
    
    # Testa detecção de smurf
    print("\nTestando detecção de smurf:")
    smurf = {
        'nickname': 'PossivelSmurf',
        'regiao': 'BR',
        'estatisticas': {
            'mmr': 2500,
            'kills': 30,
            'deaths': 2,
            'vitorias': 18,
            'partidas_jogadas': 20,
            'ping_medio': 20,
            'comportamento': 5,
            'abandonos': 0,
            'reports': 0,
            'estilo_jogo': 'Agressivo',
            'mmr_historico': [1000, 1500, 2000, 2300, 2500]
        }
    }
    eh_smurf, prob = sistema.detectar_smurf(smurf)
    print(f"É smurf: {eh_smurf}")
    print(f"Probabilidade: {prob:.2f}")
    
    # Testa agrupamento
    print("\nTestando agrupamento de jogadores:")
    grupos = sistema.agrupar_jogadores(dados_treinamento)
    print(f"Número de grupos: {len(grupos)}")
    for grupo, jogadores in grupos.items():
        print(f"\nGrupo {grupo}: {len(jogadores)} jogadores")
        mmr_medio = np.mean([j['estatisticas']['mmr'] for j in jogadores])
        mmr_min = np.min([j['estatisticas']['mmr'] for j in jogadores])
        mmr_max = np.max([j['estatisticas']['mmr'] for j in jogadores])
        print(f"  MMR médio: {mmr_medio:.2f}")
        print(f"  MMR mínimo: {mmr_min}")
        print(f"  MMR máximo: {mmr_max}")
    
    print("\nTreinamento concluído com sucesso!")

if __name__ == "__main__":
    main() 