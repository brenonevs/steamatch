# 🎮 SteamMatch - Análise de Compatibilidade Steam

## 📋 Índice
- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Começando](#-começando)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Uso](#-uso)
- [Exemplos](#-exemplos)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

## 🎯 Sobre o Projeto
SteamMatch é uma ferramenta Python que permite analisar e comparar perfis do Steam, encontrando jogos em comum e gerando estatísticas detalhadas sobre os hábitos de jogo dos usuários. O projeto utiliza a API oficial do Steam para coletar dados em tempo real.

## ⭐ Funcionalidades

### Análise de Usuários 👥
- Busca de perfis por username ou Steam ID
- Visualização detalhada de informações do perfil
- Análise de biblioteca de jogos
- Histórico de jogos recentes
- Nível Steam e conquistas

### Comparação entre Usuários 🤝
- Jogos em comum
- Tempo total de jogo compartilhado
- Análise de compatibilidade
- Sugestões de jogos multiplayer

### Estatísticas Detalhadas 📊
- Tempo total de jogo
- Jogos mais jogados
- Gêneros favoritos
- Períodos de atividade
- Conquistas desbloqueadas

## 🛠 Tecnologias
- Python 3.8+
- Steam Web API
- BeautifulSoup4
- Requests
- Type Hints
- Decorators

## 🚀 Começando

### Pré-requisitos
- Python 3.8 ou superior
- Steam API Key

### Instalação
1. Clone o repositório
```bash
git clone https://github.com/brenonevs/steamatch.git
cd steamatch
```

2. Instale as dependências
```bash
pip install -r requirements.txt
```

3. Configure sua Steam API Key
```bash
export STEAM_API_KEY="sua_api_key_aqui"
```

## 📁 Estrutura do Projeto
```bash
src/
├── models/
│ ├── user.py # Classe de usuário Steam
│ └── game.py # Classe de jogos
├── services/
│ ├── compatibility.py # Serviço de compatibilidade
│ ├── statistics.py # Análise estatística
│ └── social.py # Funcionalidades sociais
├── utils/
│ ├── cache.py # Sistema de cache
│ └── constants.py # Constantes do projeto
├── api.py # Interface com API Steam
└── main.py # Ponto de entrada
```


## 💻 Uso

### Exemplo Básico
```python
from user import SteamUser

# Criar instâncias de usuário
user1 = SteamUser(username="usuario1")
user2 = SteamUser(steam_id="76561198085937034")

# Comparar jogos
user1.compare_games_with(user2, num_games=15)
```

## 📊 Exemplos

### Comparação de Jogos
```bash
🎮 ANÁLISE DE JOGOS EM COMUM NO STEAM 🎮
==================================================
👥 USUÁRIOS ANALISADOS:
👤 Jogador 1: Usuario1
👤 Jogador 2: Usuario2
📊 ESTATÍSTICAS GERAIS:
📚 Total de jogos em comum: 42
⏰ Tempo total de jogo: 1234.5 horas
```


## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie sua Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença
Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE.md](LICENSE.md) para detalhes.

## 👨‍💻 Autor
Seu Nome - [brenonevs](https://github.com/brenonevs)

## 🙏 Agradecimentos
- Steam API
- Comunidade Python
- Contribuidores do projeto

## 📞 Contato
- Email: brenobraganevs@gmail.com
- LinkedIn: [Breno Braga](https://www.linkedin.com/in/breno-neves-31189925b/)

---
⌨️ com ❤️ por [Breno Braga](https://github.com/brenonevs) 😊