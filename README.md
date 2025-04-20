# Sistema de Matchmaking com IA

Este é um sistema de matchmaking para jogos que utiliza inteligência artificial para criar partidas equilibradas e justas.

## Funcionalidades

### Sistema de Matchmaking
- Matchmaking baseado em ELO/MMR
- Sistema de fila com tempo de espera de 30 segundos
- Agrupamento de jogadores usando clustering
- Cálculo de ELO pós-partida
- Simulação de partidas com estatísticas detalhadas

### Inteligência Artificial
- Agrupamento de jogadores baseado em múltiplas características:
  - MMR (Elo)
  - K/D Ratio
  - Win Rate
  - Ping médio
  - Toxicidade
- Detecção de smurfs
- Detecção de comportamento tóxico
- Predição de performance

### Banco de Dados
- Armazenamento de jogadores e suas estatísticas
- Histórico de partidas
- Atualização de ELO
- Persistência de dados entre sessões

### Sistema de Partidas
- Simulação de partidas com estatísticas realistas
- Cálculo de vencedor baseado em kills
- Estatísticas detalhadas por partida:
  - Kills
  - Deaths
  - Assists
  - Tempo de partida
  - Ping

## Como Usar

1. Inicie o servidor:
```bash
python server.py
```

2. Em terminais separados, inicie os clients:
```bash
python client.py
```

3. Em cada client:
   - Faça login com um nickname
   - Entre na fila de matchmaking
   - O sistema aguardará 30 segundos para encontrar o melhor match
   - Após a partida, o ELO será atualizado automaticamente

## Requisitos

- Python 3.8+
- Flask
- Flask-SocketIO
- scikit-learn
- numpy
- SQLite3

## Estrutura do Projeto

- `server.py`: Servidor principal com lógica de matchmaking
- `ia_matchmaking.py`: Sistema de IA para agrupamento e análise
- `database.py`: Gerenciamento do banco de dados
- `game.py`: Simulação de partidas
- `client.py`: Cliente para interação com o servidor

## Logs e Monitoramento

O sistema possui logs detalhados para:
- Conexões de jogadores
- Entrada/saída da fila
- Agrupamento de jogadores
- Resultados de partidas
- Atualizações de ELO
- Erros e exceções

## Próximos Passos

- Implementar sistema de ranks
- Adicionar mais métricas para matchmaking
- Melhorar a detecção de smurfs
- Adicionar sistema de premiação
- Implementar interface gráfica 