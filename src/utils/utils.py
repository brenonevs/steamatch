import os
from typing import Union, Dict, List
from functools import lru_cache
from steam_web_api import Steam

class SteamAPIError(Exception):
    """Exceção personalizada para erros da API do Steam."""
    
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
    
    def __str__(self):
        return f"Erro da API do Steam: {self.message} (Status: {self.status_code})"

class SteamService:
    """
    Classe unificada para interação com a API do Steam.
    Fornece funcionalidades para busca de usuários, jogos, estatísticas e comparações.
    
    Attributes:
        KEY (str): Chave de API do Steam obtida das variáveis de ambiente.
        steam (Steam): Instância do cliente Steam para comunicação com a API.
    
    Raises:
        ValueError: Se a STEAM_API_KEY não for encontrada nas variáveis de ambiente.
    """

    def __init__(self):
        """Inicializa o serviço Steam com a chave da API."""
        self.KEY = os.environ.get("STEAM_API_KEY")
        if not self.KEY:
            print("❌ STEAM_API_KEY não encontrada nas variáveis de ambiente")
            raise ValueError("STEAM_API_KEY não encontrada nas variáveis de ambiente")
       
        self.all_filters = (
            "basic,controller_support,fullgame,legal_notice,developers,"
            "demos,price_overview,metacritic,categories,genres,"
            "screenshots,movies,recommendations,achievements"
        )
        self.steam = Steam(self.KEY)

    @staticmethod
    def _handle_api_error(operation: str):
        """
        Decorator para tratamento padronizado de erros da API.
        
        Args:
            operation (str): Nome da operação sendo executada
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"\n❌ Erro durante {operation}: {str(e)}")
                    status_code = getattr(e, 'status_code', 400)
                    raise SteamAPIError(
                        message=f"Falha ao executar {operation}: {str(e)}",
                        status_code=status_code
                    )
            return wrapper
        return decorator
    
    # Métodos relacionados a usuários

    @_handle_api_error("busca de conquistas")
    def get_user_badges(self, steamid: Union[str, int]) -> List[Dict]:
        """Obtém as conquistas do usuário."""
        return self.steam.users.get_user_badges(str(steamid))
    
    @_handle_api_error("busca de jogos recentes")
    def get_recently_played_games(self, steamid: Union[str, int]) -> List[Dict]:
        """Obtém os últimos jogos jogados pelo usuário."""
        return self.steam.users.get_user_recently_played_games(str(steamid))
    
    @_handle_api_error("busca de lista de amigos")
    def get_friends_list(self, steamid: Union[str, int], enriched: bool = True) -> List[Dict]:
        """Obtém a lista de amigos do usuário."""
        return self.steam.users.get_user_friends_list(str(steamid), enriched)
    
    @_handle_api_error("busca de nome de usuário")
    def get_username(self, steamid: Union[str, int]) -> str:
        """Obtém o nome de usuário a partir do Steam ID."""
        if not isinstance(steamid, str):
            print(f"❌ Tipo inválido para steamid: {type(steamid)}")
            raise ValueError("Steam ID deve ser uma string")
            
        username = self.steam.users.get_username(str(steamid))
        print(f"✅ Nome de usuário encontrado: {username}")
        return username

    @_handle_api_error("busca de Steam ID")
    def get_steamid(self, username: str) -> str:
        """Obtém o Steam ID a partir do nome de usuário."""
        if not isinstance(username, str):
            print(f"❌ Tipo inválido para username: {type(username)}")
            raise ValueError("Username deve ser uma string")
            
        steamid = str(self.steam.users.get_steamid(username)["steamid"])
        print(f"✅ Steam ID encontrado: {steamid}")
        return steamid
    
    @_handle_api_error("busca de detalhes do usuário")
    @lru_cache(maxsize=100)
    def get_user_details(self, steamid: Union[str, int]) -> Dict:
        """Obtém detalhes do perfil do usuário com cache."""
        return self.steam.users.get_user_details(str(steamid))
    
    @_handle_api_error("busca de jogos do usuário")
    def get_user_games(self, steamid: Union[str, int], include_details: bool = False) -> List[Dict]:
        """Obtém lista de jogos do usuário."""
        try:
            games = self.steam.users.get_owned_games(
                steam_id=str(steamid),
                include_appinfo=include_details,
                includ_free_games=True
            )
            if include_details:
                return [
                    {**game, 'details': self.get_game_info(game['appid'])}
                    for game in games
                ]
            return games
        except Exception as e:
            print(f"❌ Erro ao buscar jogos: {e}")
            raise
    
    # Métodos relacionados a jogos
    
    @_handle_api_error("busca de informações do jogo")
    @lru_cache(maxsize=500)
    def get_game_info(self, appid: Union[str, int]) -> Dict:
        """
        Obtém informações básicas de um jogo.
        
        Returns:
            Dict contendo: nome, descrição, tipo, idade requerida, gratuito
        """
        response = self.steam.apps.get_app_details(str(appid), filters=self.all_filters)
        game_data = response[str(appid)]['data']
        
        return {
            'name': game_data.get('name'),
            'type': game_data.get('type'),
            'description': game_data.get('short_description'),
            'required_age': game_data.get('required_age'),
            'is_free': game_data.get('is_free', False)
        }
    
    @_handle_api_error("busca de conquistas")
    def get_game_achievements(self, appid: Union[str, int]) -> Dict:
        """
        Obtém informações sobre as conquistas do jogo.
        
        Returns:
            Dict contendo detalhes das conquistas disponíveis
        """
        response = self.steam.apps.get_app_details(str(appid), filters=self.all_filters)
        return response[str(appid)]['data'].get('achievements', {})
    
    @_handle_api_error("busca de requisitos")
    def get_game_requirements(self, appid: Union[str, int]) -> Dict:
        """
        Obtém requisitos do sistema para o jogo.
        
        Returns:
            Dict contendo requisitos para PC, Mac e Linux
        """
        response = self.steam.apps.get_app_details(str(appid), filters=self.all_filters)
        game_data = response[str(appid)]['data']
        
        return {
            'pc': game_data.get('pc_requirements', {}),
            'mac': game_data.get('mac_requirements', {}),
            'linux': game_data.get('linux_requirements', {})
        }
    
    @_handle_api_error("busca de mídia")
    def get_game_media(self, appid: Union[str, int]) -> Dict:
        """
        Obtém screenshots e vídeos do jogo.
        
        Returns:
            Dict contendo screenshots e vídeos disponíveis
        """
        response = self.steam.apps.get_app_details(str(appid), filters=self.all_filters)
        game_data = response[str(appid)]['data']
        
        return {
            'screenshots': game_data.get('screenshots', []),
            'movies': game_data.get('movies', [])
        }
    
    @_handle_api_error("busca de preço")
    def get_game_price(self, appid: Union[str, int]) -> Dict:
        """
        Obtém informações de preço do jogo.
        
        Returns:
            Dict contendo preço atual, inicial e desconto
        """
        response = self.steam.apps.get_app_details(str(appid), filters=self.all_filters)
        price_data = response[str(appid)]['data']['price_overview']
        
        return {
            'currency': price_data.get('currency'),
            'initial': price_data.get('initial'),
            'final': price_data.get('final'),
            'discount_percent': price_data.get('discount_percent', 0),
            'final_formatted': price_data.get('final_formatted')
        }
    
    @_handle_api_error("busca de detalhes completos")
    def get_game_full_details(self, appid: Union[str, int]) -> Dict:
        """
        Obtém todos os detalhes disponíveis sobre o jogo.
        
        Returns:
            Dict contendo todas as informações disponíveis do jogo
        """
        
        response = self.steam.apps.get_app_details(str(appid), filters=self.all_filters)
        if not response[str(appid)].get('success'):
            raise ValueError(f"Não foi possível obter detalhes do jogo {appid}")
            
        return response[str(appid)]['data']
    
    @_handle_api_error("busca de categorias e gêneros")
    def get_game_categories(self, appid: Union[str, int]) -> Dict:
        """
        Obtém categorias e gêneros do jogo.
        
        Returns:
            Dict contendo categorias e gêneros do jogo
        """
        response = self.steam.apps.get_app_details(str(appid), filters=self.all_filters )
        game_data = response[str(appid)]['data']
        
        return {
            'categories': game_data.get('categories', []),
            'genres': game_data.get('genres', []),
            'supported_languages': game_data.get('supported_languages', '')
        }

    # Métodos de descoberta e comparação
    def get_games_in_common(self, steamid1: Union[str, int], steamid2: Union[str, int]) -> List[Dict]:
        """Obtém jogos em comum entre dois usuários com detalhes completos."""
        print("\n🔄 Iniciando busca de jogos em comum...")
        print("=" * 50)
        
        # Buscando jogos dos usuários
        print(f"📚 Buscando biblioteca do usuário 1 (ID: {steamid1})")
        user1_games = self.get_user_games(steamid1)
        print(f"✅ Encontrados {user1_games['game_count']} jogos para usuário 1")
        
        print(f"📚 Buscando biblioteca do usuário 2 (ID: {steamid2})")
        user2_games = self.get_user_games(steamid2)
        print(f"✅ Encontrados {user2_games['game_count']} jogos para usuário 2")
        
        # Processando dados
        print("\n🔄 Processando bibliotecas...")
        games1 = user1_games.get('games', []) if isinstance(user1_games, dict) else user1_games
        games2 = user2_games.get('games', []) if isinstance(user2_games, dict) else user2_games
        
        games1_dict = {game['appid']: game for game in games1}
        games2_dict = {game['appid']: game for game in games2}

        common_app_ids = set(games1_dict.keys()) & set(games2_dict.keys())
        print(f"🎯 Encontrados {len(common_app_ids)} jogos em comum!")
        
        # Coletando detalhes dos jogos em comum
        return self._process_common_games(common_app_ids, games1_dict, games2_dict)

    def _process_common_games(self, common_app_ids: set, games1_dict: Dict, games2_dict: Dict) -> List[Dict]:
        """Processa os jogos em comum e coleta seus detalhes."""
        print("\n📊 Coletando detalhes dos jogos em comum...")
        common_games = []
        total_games = len(common_app_ids)
        
        for idx, appid in enumerate(common_app_ids, 1):
            progress = (idx / total_games) * 100
            print(f"\r⏳ Progresso: {progress:.1f}% ({idx}/{total_games} jogos)", end="")
            
            try:
                game_details = self.get_game_info(appid)
                game_info = self._create_game_info(appid, game_details, games1_dict, games2_dict)
                common_games.append(game_info)
            except Exception as e:
                print(f"\n⚠️ Aviso: Erro ao processar jogo {appid}: {str(e)}")
                game_info = self._create_basic_game_info(appid, games1_dict, games2_dict)
                common_games.append(game_info)
        
        print("\n✨ Ordenando resultados por tempo de jogo...")
        common_games.sort(key=lambda x: x['total_playtime_hours'], reverse=True)
        
        print("✅ Processamento concluído com sucesso!")
        return common_games

    def print_common_games(self, steamid1: Union[str, int], steamid2: Union[str, int], num_games: int = 10):
        """Imprime uma lista formatada dos jogos em comum entre dois usuários."""
        print(f"\n📊 Preparando análise dos top {num_games} jogos...")
        print("\n" + "="*50)
        print("🎮 ANÁLISE DE JOGOS EM COMUM NO STEAM 🎮")
        print("="*50)
        
        # Obtendo detalhes dos usuários
        print("\n🔍 Buscando informações dos perfis...")
        user1_details = self.get_user_details(steamid1)
        user2_details = self.get_user_details(steamid2)
        
        user1_name = user1_details['player']['personaname']
        user2_name = user2_details['player']['personaname']
        
        print("\n👥 USUÁRIOS ANALISADOS:")
        print(f"👤 Jogador 1: {user1_name}")
        print(f"👤 Jogador 2: {user2_name}")
        
        # Buscando jogos
        print("\n🎲 INICIANDO ANÁLISE DE BIBLIOTECAS")
        print("⏳ Isso pode levar alguns minutos...")
        common_games = self.get_games_in_common(steamid1, steamid2)
        
        # Estatísticas gerais
        total_games = len(common_games)
        total_hours = sum(game['total_playtime_hours'] for game in common_games)
        
        print("\n📊 ESTATÍSTICAS GERAIS:")
        print(f"📚 Total de jogos em comum: {total_games}")
        print(f"⏰ Tempo total de jogo: {total_hours:.1f} horas")
        
        # Configuração da tabela
        print("\n📊 Preparando exibição dos resultados...")
        name1_width = max(len(user1_name), 15)
        name2_width = max(len(user2_name), 15)
        game_width = 40
        time_width = 12
        
        total_width = game_width + (time_width * 3) + 3
        
        # Exibição dos resultados
        print("\n🏆 RESULTADOS DA ANÁLISE 🏆")
        print("=" * total_width)
        
        # Cabeçalho
        header = (
            f"{'Nome do Jogo':<{game_width}} "
            f"{user1_name:^{time_width}} "
            f"{user2_name:^{time_width}} "
            f"{'Tempo Total':^{time_width}}"
        )
        
        subheader = (
            f"{'':<{game_width}} "
            f"{'(horas)':^{time_width}} "
            f"{'(horas)':^{time_width}} "
            f"{'(horas)':^{time_width}}"
        )
        
        print(header)
        print(subheader)
        print("=" * total_width)
        
        # Exibindo jogos
        print("\n🏆 TOP JOGOS MAIS JOGADOS:")
        games_to_show = min(num_games, len(common_games))
        
        for i, game in enumerate(common_games[:games_to_show], 1):
            position_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            total_time = game['total_playtime_hours']
            
            # Emoji baseado no tempo de jogo
            time_emoji = "💎" if total_time > 1000 else "⭐" if total_time > 100 else "🌟" if total_time > 50 else "✨"
            
            # Status de atividade
            activity_emoji = "🔥" if (game['user1_playtime_hours'] > 0 and game['user2_playtime_hours'] > 0) else "💤"
            
            print(
                f"{position_emoji} "
                f"{game['name'][:game_width-3]:<{game_width-3}} "
                f"{game['user1_playtime_hours']:>{time_width-1}.1f}h "
                f"{game['user2_playtime_hours']:>{time_width-1}.1f}h "
                f"{game['total_playtime_hours']:>{time_width-1}.1f}h {time_emoji} {activity_emoji}"
            )
        
        print("=" * total_width)
        print(f"\n📝 LEGENDA:")
        print("💎 = Mais de 1000 horas jogadas")
        print("⭐ = Mais de 100 horas jogadas")
        print("🌟 = Mais de 50 horas jogadas")
        print("✨ = Menos de 50 horas jogadas")
        print("🔥 = Jogado recentemente por ambos")
        print("💤 = Sem atividade recente")
        
        print("\n✅ ANÁLISE CONCLUÍDA COM SUCESSO! ✅")
        print("="*50)

    def _create_game_info(self, appid: str, game_details: Dict, games1_dict: Dict, games2_dict: Dict) -> Dict:
        """
        Cria informações detalhadas de um jogo.
        
        Args:
            appid: ID do jogo
            game_details: Detalhes do jogo da API
            games1_dict: Dicionário de jogos do usuário 1
            games2_dict: Dicionário de jogos do usuário 2
        
        Returns:
            Dict: Informações formatadas do jogo
        """
        return {
            'appid': appid,
            'name': game_details['name'],
            'description': game_details['description'],
            'about_the_game': game_details['about_the_game'],
            'pc_requirements': game_details['pc'],
            'mac_requirements': game_details['mac'],
            'linux_requirements': game_details['linux'],
            'required_age': game_details['required_age'],
            'user1_playtime_hours': round(games1_dict[appid]['playtime_forever'] / 60, 2),
            'user2_playtime_hours': round(games2_dict[appid]['playtime_forever'] / 60, 2),
            'total_playtime_hours': round((games1_dict[appid]['playtime_forever'] + 
                                        games2_dict[appid]['playtime_forever']) / 60, 2),
            'details': game_details
        }

    def _create_basic_game_info(self, appid: str, games1_dict: Dict, games2_dict: Dict) -> Dict:
        """
        Cria informações básicas de um jogo quando os detalhes completos não estão disponíveis.
        
        Args:
            appid: ID do jogo
            games1_dict: Dicionário de jogos do usuário 1
            games2_dict: Dicionário de jogos do usuário 2
        
        Returns:
            Dict: Informações básicas do jogo
        """
        return {
            'appid': appid,
            'name': f"Jogo {appid}",
            'description': f"Descrição não encontrada para o jogo {appid}",
            'about_the_game': f"Sobre o jogo não encontrado para o jogo {appid}",
            'pc_requirements': f"Requisitos não encontrados para o jogo {appid}",
            'mac_requirements': f"Requisitos não encontrados para o jogo {appid}",
            'linux_requirements': f"Requisitos não encontrados para o jogo {appid}",
            'required_age': f"Idade não encontrada para o jogo {appid}",
            'user1_playtime_hours': round(games1_dict[appid]['playtime_forever'] / 60, 2),
            'user2_playtime_hours': round(games2_dict[appid]['playtime_forever'] / 60, 2),
            'total_playtime_hours': round((games1_dict[appid]['playtime_forever'] + 
                                        games2_dict[appid]['playtime_forever']) / 60, 2)
        }


