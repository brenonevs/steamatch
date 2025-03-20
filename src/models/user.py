from typing import List, Dict
from api import SteamUtils, SteamGameDiscoveryService

class SteamUser:
    """
    Classe que representa um usuário do Steam com suas funcionalidades.
    """
    def __init__(self, username: str = None, steam_id: str = None):
        """
        Inicializa um usuário do Steam.
        
        Args:
            username: Nome de usuário do Steam
            steam_id: ID do Steam (opcional se username for fornecido)
        """
        self.steam_utils = SteamUtils()
        self._username = username
        self._steam_id = steam_id
        self._profile_details = None
        self._games = None
        
        if username and not steam_id:
            print(f"🔍 Buscando Steam ID para usuário: {username}")
            self._steam_id = self.steam_utils.get_steamid(username)
        elif steam_id and not username:
            print(f"🔍 Buscando nome de usuário para Steam ID: {steam_id}")
            self._username = self.steam_utils.get_user_details(steam_id)["player"]["personaname"]

    @property
    def friends_list(self) -> str:
        """Retorna a lista de amigos do usuário."""
        return self.steam_utils.get_friends_list(self._steam_id)

    @property
    def steam_id(self) -> str:
        """Retorna o Steam ID do usuário."""
        return self._steam_id
    
    @property
    def profile_details(self) -> Dict:
        """Obtém e armazena em cache os detalhes do perfil."""
        if not self._profile_details:
            print("📱 Buscando detalhes do perfil...")
            self._profile_details = self.steam_utils.get_user_details(self._steam_id)
        return self._profile_details
    
    @property
    def get_games(self) -> List[Dict]:
        """Obtém e armazena em cache os jogos do usuário."""
        if not self._games:
            print(f"🎮 Carregando biblioteca de jogos para o usuário {self._username}...")
            self._games = self.steam_utils.get_user_games(self._steam_id)
        return self._games
    
    def compare_games_with(self, other_user: 'SteamUser', num_games: int = 10) -> None:
        """
        Compara jogos com outro usuário.
        
        Args:
            other_user: Outro usuário do Steam para comparação
            num_games: Número de jogos a serem exibidos na comparação
        """
        discovery_service = SteamGameDiscoveryService()
        discovery_service.print_common_games(self.steam_id, other_user.steam_id, num_games)
    
    