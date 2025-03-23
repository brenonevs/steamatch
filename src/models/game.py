from typing import List, Dict, Optional
from utils.utils import SteamService

class SteamGame:
    """
    Classe que representa um jogo do Steam com suas funcionalidades.
    
    Attributes:
        app_id (str): ID do jogo na Steam
        steam_utils (SteamService): Instância do serviço Steam
        _basic_info (Dict): Cache das informações básicas
        _full_details (Dict): Cache dos detalhes completos
        _requirements (Dict): Cache dos requisitos do sistema
        _media (Dict): Cache da mídia do jogo
        _categories (Dict): Cache das categorias e gêneros
        _price (Dict): Cache das informações de preço
        _achievements (Dict): Cache das conquistas
    """

    def __init__(self, app_id_or_name: str, steam_utils: Optional[SteamService] = None):
        """
        Inicializa um jogo do Steam.
        
        Args:
            app_id_or_name: ID do jogo na Steam ou nome do jogo
            steam_utils: Instância de SteamUtils (opcional)
        """
        self.steam_utils = steam_utils or SteamService()
        
        # Verifica se o input é um ID (apenas números) ou nome
        if app_id_or_name.isdigit():
            self.app_id = app_id_or_name
        else:
            print(f"🔍 Buscando ID para o jogo: {app_id_or_name}")
            self.app_id = self.search_game_id(app_id_or_name)
            
        # Inicialização dos caches
        self._basic_info = None
        self._full_details = None
        self._requirements = None
        self._media = None
        self._categories = None
        self._price = None
        self._achievements = None
        
        print(f"🎮 Inicializando jogo com ID: {self.app_id}")

    # Métodos estáticos
    @staticmethod
    def search_game_id(game_name: str) -> str:
        """
        Busca o ID do jogo pelo nome.
        
        Args:
            game_name: Nome do jogo
            
        Returns:
            str: ID do jogo encontrado
            
        Raises:
            ValueError: Se nenhum jogo for encontrado
        """
        try:
            steam_utils = SteamService()
            results = steam_utils.steam.apps.search_games(game_name)
            if not results.get('apps'):
                raise ValueError(f"Nenhum jogo encontrado com o nome: {game_name}")
            
            return str(results['apps'][0]['id'][0])
        except Exception as e:
            print(f"❌ Erro ao buscar ID do jogo: {str(e)}")
            raise

    # Properties básicas
    @property
    def basic_info(self) -> Dict:
        """Obtém e armazena em cache as informações básicas do jogo."""
        if not self._basic_info:
            print(f"📋 Buscando informações básicas do jogo {self.app_id}...")
            self._basic_info = self.steam_utils.get_game_info(self.app_id)
        return self._basic_info

    @property
    def name(self) -> str:
        """Retorna o nome do jogo."""
        return self.basic_info.get('name', 'Nome não encontrado')

    @property
    def description(self) -> str:
        """Retorna a descrição do jogo."""
        return self.basic_info.get('description', 'Descrição não encontrada')

    @property
    def type(self) -> str:
        """Retorna o tipo do jogo."""
        return self.basic_info.get('type', 'Tipo não encontrado')

    @property
    def is_free(self) -> bool:
        """Retorna se o jogo é gratuito."""
        return self.basic_info.get('is_free', False)

    # Properties com cache
    @property
    def full_details(self) -> Dict:
        """Obtém e armazena em cache todos os detalhes do jogo."""
        if not self._full_details:
            print(f"📚 Buscando detalhes completos do jogo {self.app_id}...")
            self._full_details = self.steam_utils.get_game_full_details(self.app_id)
        return self._full_details

    @property
    def requirements(self) -> Dict:
        """Obtém e armazena em cache os requisitos do sistema."""
        if not self._requirements:
            print(f"💻 Buscando requisitos do sistema para {self.app_id}...")
            self._requirements = self.steam_utils.get_game_requirements(self.app_id)
        return self._requirements

    @property
    def media(self) -> Dict:
        """Obtém e armazena em cache as mídias do jogo."""
        if not self._media:
            print(f"🎬 Buscando mídia para {self.app_id}...")
            self._media = self.steam_utils.get_game_media(self.app_id)
        return self._media

    @property
    def categories(self) -> Dict:
        """Obtém e armazena em cache as categorias e gêneros."""
        if not self._categories:
            print(f"🏷️ Buscando categorias para {self.app_id}...")
            self._categories = self.steam_utils.get_game_categories(self.app_id)
        return self._categories

    @property
    def price(self) -> Dict:
        """Obtém e armazena em cache as informações de preço."""
        if not self._price:
            print(f"💰 Buscando informações de preço para {self.app_id}...")
            self._price = self.steam_utils.get_game_price(self.app_id)
        return self._price

    @property
    def achievements(self) -> Dict:
        """Obtém e armazena em cache as conquistas do jogo."""
        if not self._achievements:
            print(f"🏆 Buscando conquistas para {self.app_id}...")
            self._achievements = self.steam_utils.get_game_achievements(self.app_id)
        return self._achievements

    # Métodos de acesso direto aos dados
    def get_screenshots(self) -> List[Dict]:
        """Retorna as screenshots do jogo."""
        return self.media.get('screenshots', [])

    def get_movies(self) -> List[Dict]:
        """Retorna os vídeos do jogo."""
        return self.media.get('movies', [])

    def get_genres(self) -> List[Dict]:
        """Retorna os gêneros do jogo."""
        return self.categories.get('genres', [])

    def get_supported_languages(self) -> str:
        """Retorna os idiomas suportados."""
        return self.categories.get('supported_languages', '')

    def get_pc_requirements(self) -> Dict:
        """Retorna os requisitos para PC."""
        return self.requirements.get('pc', {})

    def get_mac_requirements(self) -> Dict:
        """Retorna os requisitos para Mac."""
        return self.requirements.get('mac', {})

    def get_linux_requirements(self) -> Dict:
        """Retorna os requisitos para Linux."""
        return self.requirements.get('linux', {})
    
    # Métodos especiais
    def __str__(self) -> str:
        """Retorna uma representação em string do jogo."""
        return f"{self.name} (ID: {self.app_id})"

    def __repr__(self) -> str:
        """Retorna uma representação oficial do objeto."""
        return f"SteamGame(app_id='{self.app_id}')"