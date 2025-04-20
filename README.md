# Sistema de Matchmaking Inteligente com IA

Este é um sistema avançado de matchmaking que utiliza técnicas de Inteligência Artificial para criar partidas equilibradas e agradáveis.

## Funcionalidades

### 🤖 Inteligência Artificial
- Predição de performance com Random Forest
- Clustering de jogadores com K-Means
- Sistema de recomendação de teammates
- Detecção de smurfs e comportamento tóxico
- Aprendizado contínuo com novos dados

### 👤 Perfil do Jogador
- Cadastro com nickname único
- Seleção de plataforma (PC, PS4, XBOX, MOBILE)
- Seleção de região (Brasil, América do Norte, Europa, Ásia)
- Estilo de jogo (Agressivo, Defensivo, Suporte, Híbrido)
- Sistema de comportamento e reputação

### 🎮 Sistema de Matchmaking
- Algoritmo de pareamento multi-fatorial
- Consideração de MMR (Match Making Rating)
- Análise de latência e região
- Compatibilidade de estilo de jogo
- Sistema de comportamento e abandono
- Score de compatibilidade entre jogadores

### 📊 Estatísticas e Ranking
- Sistema MMR dinâmico
- K/D Ratio e Win Rate
- Histórico de ping e latência
- Taxa de abandono
- Comportamento e reputação
- Histórico completo de partidas

### ⚖️ Balanceamento
- Pesos configuráveis para diferentes fatores
- Ajuste dinâmico do MMR baseado no comportamento
- Consideração de compatibilidade de estilos
- Prevenção de abandono e má conduta

### 💾 Persistência
- Salvamento automático de dados
- Histórico de MMR
- Registro de comportamento
- Backup de estatísticas
- Modelos de IA persistentes

## Requisitos

- Python 3.8+
- Dependências listadas em `requirements.txt`

## Como usar

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Execute o programa:
```bash
python game.py
```

## Estrutura do Código

- `SistemaIA`: Classe principal de IA com todos os modelos
- `Plataforma`: Enum com as plataformas suportadas
- `Regiao`: Enum com as regiões disponíveis
- `EstiloJogo`: Enum com os estilos de jogo
- `Comportamento`: Enum com níveis de comportamento
- `Estatisticas`: Classe para gerenciar métricas do jogador
- `Jogador`: Classe que representa um jogador com seu perfil
- `SistemaMatchmaking`: Sistema principal de pareamento

## Como funciona

1. **Predição de Performance**:
   - Usa Random Forest para prever MMR futuro
   - Considera múltiplas features do jogador
   - Ajusta probabilidades de vitória

2. **Clustering de Jogadores**:
   - Agrupa jogadores similares usando K-Means
   - Considera MMR, K/D, Win Rate, etc.
   - Usado para recomendações de teammates

3. **Detecção de Smurfs**:
   - Analisa padrões suspeitos
   - Win rate muito alta
   - K/D ratio elevado
   - MMR subindo rápido
   - Poucas partidas jogadas

4. **Detecção de Toxicidade**:
   - Monitora taxa de abandono
   - Conta número de reports
   - Avalia comportamento geral
   - Ajusta matchmaking

5. **Recomendação de Teammates**:
   - Usa clustering para encontrar jogadores similares
   - Calcula score de compatibilidade
   - Considera múltiplos fatores
   - Aprende com o tempo

## Exemplo de Saída

O programa mostrará:
- Score de compatibilidade entre jogadores
- Predição de performance para cada jogador
- Estatísticas detalhadas de cada partida
- Ranking por MMR
- Alertas de smurf/toxicidade
- Métricas de comportamento
- Histórico de performance 