import os
from bs4 import BeautifulSoup
from typing import Union, Dict, List, Optional
from functools import lru_cache
from steam_web_api import Steam


class SteamUtils:
    """Classe utilitária para interação com a API do Steam.
    
    Esta classe fornece métodos para acessar várias funcionalidades da API do Steam,
    incluindo busca de usuários, jogos e estatísticas.
    
    Attributes:
        KEY (str): Chave de API do Steam obtida das variáveis de ambiente.
        steam (Steam): Instância do cliente Steam para comunicação com a API.
    
    Raises:
        ValueError: Se a STEAM_API_KEY não for encontrada nas variáveis de ambiente.
    """

    def __init__(self):
        """Inicializa a classe SteamUtils.
        
        Configura o logger e inicializa a conexão com a API do Steam.
        """
        self.KEY = os.environ.get("STEAM_API_KEY")
        if not self.KEY:
            print("❌ STEAM_API_KEY não encontrada nas variáveis de ambiente")
            raise ValueError("STEAM_API_KEY não encontrada nas variáveis de ambiente")
       
        self.steam = Steam(self.KEY)

    @staticmethod
    def _handle_api_error(operation: str):
        """Decorator para tratamento padronizado de erros da API.
        
        Args:
            operation (str): Nome da operação sendo executada.
            
        Returns:
            Callable: Função decoradora que trata erros.
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    print(f"\n❌ Erro durante {operation}: {str(e)}")
                    status_code = getattr(e, 'status_code', 400)
                    raise SteamAPIError(
                        message=f"Falha ao executar {operation}: {str(e)}",
                        status_code=status_code
                    )
            return wrapper
        return decorator
    
    @_handle_api_error("busca de lista de amigos")
    def get_friends_list(self, steamid: Union[str, int], enriched: bool = True) -> List[Dict]:
        """Obtém a lista de amigos do usuário.

        Args:
            steamid: ID do usuário no Steam
            enriched: Se True, inclui detalhes dos amigos
        
        Returns:
            List[Dict]: Lista de amigos do usuário
        
        """
        return self.steam.users.get_user_friends_list(str(steamid), enriched)
    
    @_handle_api_error("busca de nome de usuário")
    def get_username(self, steamid: Union[str, int]) -> str:
        """Obtém o nome de usuário a partir do Steam ID.
        
        Args:
            steamid: ID do usuário no Steam
        
        Returns:
            str: Nome de usuário do Steam.
            
        Raises:
            ValueError: Se o steamid não for uma string.
            SteamAPIError: Se houver erro na comunicação com a API.
        """
        if not isinstance(steamid, str):
            print(f"❌ Tipo inválido para steamid: {type(steamid)}")
            raise ValueError("Steam ID deve ser uma string")
            
        username = self.steam.users.get_username(str(steamid))
        print(f"✅ Nome de usuário encontrado: {username}")
        return username

    @_handle_api_error("busca de Steam ID")
    def get_steamid(self, username: str) -> str:
        """Obtém o Steam ID a partir do nome de usuário.
        
        Args:
            username (str): Nome de usuário do Steam.
            
        Returns:
            str: Steam ID do usuário.
            
        Raises:
            ValueError: Se o username não for uma string.
            SteamAPIError: Se houver erro na comunicação com a API.
        """
        if not isinstance(username, str):
            print(f"❌ Tipo inválido para username: {type(username)}")
            raise ValueError("Username deve ser uma string")
            
        steamid = str(self.steam.users.get_steamid(username)["steamid"])
        print(f"✅ Steam ID encontrado: {steamid}")
        return steamid
    
    @_handle_api_error("busca de detalhes do usuário")
    @lru_cache(maxsize=100)  # Cache para resultados frequentes
    def get_user_details(self, steamid: Union[str, int]) -> Dict:
        """
        Obtém detalhes do perfil do usuário com cache
        
        Args:
            steamid: ID do usuário no Steam
            
        Returns:
            Dict: Informações do perfil do usuário
        """
        return self.steam.users.get_user_details(str(steamid))
    
    @_handle_api_error("busca de jogos do usuário")
    def get_user_games(self, steamid: Union[str, int], include_details: bool = False) -> List[Dict]:
        """
        Obtém lista de jogos do usuário com opção de detalhes
        
        Args:
            steamid: ID do usuário no Steam
            include_details: Se True, inclui detalhes de cada jogo
            
        Returns:
            List[Dict]: Lista de jogos com ou sem detalhes
        """
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
    
    @_handle_api_error("busca de informações do jogo")
    @lru_cache(maxsize=500)
    def get_game_info(self, appid: Union[str, int]) -> Dict:
        """
        Obtém informações detalhadas de um jogo com cache
        
        Args:
            appid: ID do jogo no Steam
            
        Returns:
            Dict: Informações detalhadas do jogo
        """
        return self.steam.apps.get_app_details(str(appid))
    
    @_handle_api_error("busca de conquistas")
    def get_game_achievements(self, appid: Union[str, int]) -> Dict:
        """
        Obtém lista de conquistas disponíveis para um jogo
        
        Args:
            appid: ID do jogo no Steam
            
        Returns:
            Dict: Informações sobre as conquistas do jogo
        """
        return self.steam.apps.get_game_achievements(str(appid))
    
    @_handle_api_error("busca de estatísticas do jogo")
    def get_game_stats(self, appid: Union[str, int], steamid: Union[str, int]) -> Dict:
        """
        Obtém estatísticas de um jogador em um jogo específico
        
        Args:
            appid: ID do jogo no Steam
            steamid: ID do usuário no Steam
            
        Returns:
            Dict: Estatísticas do jogador no jogo
        """
        return self.steam.apps.get_game_stats(str(appid), str(steamid))
    
    @_handle_api_error("busca de placar")
    def get_game_leaderboard(self, appid: Union[str, int], leaderboard_name: str) -> Dict:
        """
        Obtém placar de um jogo específico
        
        Args:
            appid: ID do jogo no Steam
            leaderboard_name: Nome do placar
            
        Returns:
            Dict: Informações do placar
        """
        return self.steam.apps.get_game_leaderboard(str(appid), leaderboard_name)
    
    @_handle_api_error("busca de notícias")
    def get_game_news(self, appid: Union[str, int], count: int = 3) -> Dict:
        """
        Obtém últimas notícias de um jogo
        
        Args:
            appid: ID do jogo no Steam
            count: Número de notícias para retornar
            
        Returns:
            Dict: Últimas notícias do jogo
        """
        return self.steam.apps.get_game_news(str(appid))
    
    @_handle_api_error("busca de reviews")
    def get_game_reviews(self, appid: Union[str, int], language: str = "portuguese") -> Dict:
        """
        Obtém reviews de um jogo
        
        Args:
            appid: ID do jogo no Steam
            language: Idioma das reviews
            
        Returns:
            Dict: Reviews do jogo
        """
        return self.steam.apps.get_game_reviews(str(appid))
    
    @_handle_api_error("busca de preço")
    def get_game_price(self, appid: Union[str, int], country: str = "BR") -> Dict:
        """
        Obtém preço atual de um jogo
        
        Args:
            appid: ID do jogo no Steam
            country: Código do país para preços
            
        Returns:
            Dict: Informações de preço do jogo
        """
        return self.steam.apps.get_game_price(str(appid))
    
    @_handle_api_error("busca de histórico de preços")
    def get_game_price_history(self, appid: Union[str, int]) -> Dict:
        """
        Obtém histórico de preços de um jogo
        
        Args:
            appid: ID do jogo no Steam
            
        Returns:
            Dict: Histórico de preços do jogo
        """
        return self.steam.apps.get_game_price_history(str(appid))

class SteamAPIError(Exception):
    """Exceção personalizada para erros da API do Steam"""
    
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
    
    def __str__(self):
        return f"Erro da API do Steam: {self.message} (Status: {self.status_code})"
    

class SteamGameDiscoveryService(SteamUtils):
    """Serviço para descoberta de jogos em comum entre usuários do Steam.
    
    Esta classe estende SteamUtils para fornecer funcionalidades específicas
    relacionadas à descoberta e comparação de jogos entre usuários.
    """

    def get_games_in_common(self, steamid1: Union[str, int], steamid2: Union[str, int]) -> List[Dict]:
        """Obtém jogos em comum entre dois usuários com detalhes completos."""
        
        print("\n🔄 Iniciando busca de jogos em comum...")
        print("=" * 50)
        
        # Buscando jogos do primeiro usuário
        print(f"📚 Buscando biblioteca do usuário 1 (ID: {steamid1})")
        user1_games = self.get_user_games(steamid1)
        print(f"✅ Encontrados {user1_games['game_count']} jogos para usuário 1")
        
        # Buscando jogos do segundo usuário
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
        
        print("\n📊 Coletando detalhes dos jogos em comum...")
        common_games = []
        total_games = len(common_app_ids)
        
        for idx, appid in enumerate(common_app_ids, 1):
            progress = (idx / total_games) * 100
            print(f"\r⏳ Progresso: {progress:.1f}% ({idx}/{total_games} jogos)", end="")
            
            try:
                game_details = self.get_game_info(appid)
                
                game_info = {
                    'appid': appid,
                    'name': game_details[str(appid)]['data'].get('name', 'Nome não encontrado'),
                    'description': game_details[str(appid)]['data'].get('detailed_description', 'Descrição não encontrada'),
                    'about_the_game': game_details[str(appid)]['data'].get('about_the_game', 'Sobre o jogo não encontrado'),
                    'pc_requirements': game_details[str(appid)]['data'].get('pc_requirements', 'Requisitos de sistema não encontrados'),
                    'mac_requirements': game_details[str(appid)]['data'].get('mac_requirements', 'Requisitos de sistema não encontrados'),
                    'linux_requirements': game_details[str(appid)]['data'].get('linux_requirements', 'Requisitos de sistema não encontrados'),
                    'required_age': game_details[str(appid)]['data'].get('required_age', 'Idade mínima não encontrada'),
                    'user1_playtime_hours': round(games1_dict[appid]['playtime_forever'] / 60, 2),
                    'user2_playtime_hours': round(games2_dict[appid]['playtime_forever'] / 60, 2),
                    'total_playtime_hours': round((games1_dict[appid]['playtime_forever'] + 
                                                games2_dict[appid]['playtime_forever']) / 60, 2),
                    'details': game_details
                }
                common_games.append(game_info)
                
            except Exception as e:
                print(f"\n⚠️ Aviso: Erro ao processar jogo {appid}")
                # Verifica se o erro é devido ao jogo ter sido removido
                is_removed = (game_details[str(appid)]['success'] == False)
                game_status = "[REMOVIDO]" if is_removed else ""

                if is_removed:
                    print(f'Provavelmente o jogo {appid} foi removido da Steam')
                else:
                    print(f'Erro ao buscar informações do jogo {appid}: {e}')
                
                # Adiciona versão básica se não conseguir obter os detalhes
                game_info = {
                    'appid': appid,
                    'name': game_status,
                    'description': f"Descrição não encontrada para o jogo {appid}",
                    'about_the_game': f"Sobre o jogo não encontrado para o jogo {appid}",
                    'pc_requirements': f"Requisitos de sistema não encontrados para o jogo {appid}",
                    'mac_requirements': f"Requisitos de sistema não encontrados para o jogo {appid}",
                    'linux_requirements': f"Requisitos de sistema não encontrados para o jogo {appid}",
                    'required_age': f"Idade mínima não encontrada para o jogo {appid}",
                    'is_removed': is_removed,  # Novo campo para indicar se o jogo foi removido
                    'user1_playtime_hours': round(games1_dict[appid]['playtime_forever'] / 60, 2),
                    'user2_playtime_hours': round(games2_dict[appid]['playtime_forever'] / 60, 2),
                    'total_playtime_hours': round((games1_dict[appid]['playtime_forever'] + 
                                                games2_dict[appid]['playtime_forever']) / 60, 2)
                }
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




if __name__ == "__main__":
    try:
        print("\n🚀 INICIANDO SISTEMA DE ANÁLISE STEAM 🚀")
        print("="*50)

        print("🔄 Inicializando conexão com a API do Steam...")
        steam_utils = SteamUtils()
        game_discovery_service = SteamGameDiscoveryService()
        print("✅ Conexão com API do Steam inicializada com sucesso!")
        
        print("\n👤 CONFIGURAÇÃO DOS USUÁRIOS")
        username_1 = "Breno_Bhp"
        print(f"🔍 Buscando Steam ID para: {username_1}")
        steamid1 = steam_utils.get_steamid(username_1)
        steamid2 = "76561198141766282"
        print(f"✅ IDs dos usuários validados!")
        
        num_games = 15
        game_discovery_service.print_common_games(steamid1, steamid2, num_games)
        
    except SteamAPIError as e:
        print("\n❌ ERRO NA API DO STEAM")
        print(f"📛 Mensagem: {e.message}")
        print(f"🔢 Status: {e.status_code}")
        print("💡 Dica: Verifique sua conexão e tente novamente")
    except Exception as e:
        print("\n💥 ERRO INESPERADO")
        print(f"⚠️ {str(e)}")
        print("💡 Dica: Capture a mensagem de erro e contate o suporte")
    finally:
        print("\n👋 Finalizando programa...")
        print("="*50)
    
