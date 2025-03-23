import requests
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple
import threading
from functools import partial
import concurrent.futures
from dataclasses import dataclass
import time

STEAM_API_KEY = '9E61CF132D7355A5D1CB171BED5E6FDC'
STEAM_ID = '76561198276702363'

@dataclass
class GameInfo:
    """Classe para armazenar informações de um jogo."""
    appid: int
    name: str
    playtime_forever: float = 0
    tags: Dict = None
    genres: Dict = None
    score: float = 0
    matching_tags: List = None

class SteamGameRecommender:
    """Sistema de recomendação de jogos do Steam."""
    
    def __init__(self, api_key: str, steam_id: str):
        self.api_key = api_key
        self.steam_id = steam_id
        self.user_games: List[GameInfo] = []
        self.user_profile: Dict = {}
        
    def fetch_user_library(self) -> None:
        """Busca a biblioteca de jogos do usuário."""
        print("\n📚 Buscando biblioteca do usuário...")
        
        try:
            url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
            params = {
                'key': self.api_key,
                'steamid': self.steam_id,
                'include_appinfo': True,
                'include_played_free_games': True
            }
            
            # Adiciona logs para debug
            print(f"🔄 Fazendo requisição para: {url}")
            print(f"🔑 Usando Steam ID: {self.steam_id}")
            
            response = requests.get(url, params=params, timeout=10)
            
            # Verifica o status da resposta
            print(f"📡 Status da resposta: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Erro na resposta da API: {response.text}")
                raise ValueError(f"API retornou status {response.status_code}")
            
            try:
                data = response.json()
            except ValueError as e:
                print(f"❌ Resposta não é um JSON válido: {response.text[:200]}...")
                raise
            
            if 'response' not in data:
                print(f"❌ Formato inesperado na resposta: {data}")
                raise ValueError("Formato de resposta inválido da API Steam")
            
            if 'games' not in data['response']:
                print(f"❌ Nenhum jogo encontrado na resposta: {data['response']}")
                raise ValueError("Nenhum jogo encontrado na biblioteca")
            
            raw_games = data['response']['games']
            self.user_games = [
                GameInfo(
                    appid=game['appid'],
                    name=game.get('name', f"Jogo {game['appid']}"),
                    playtime_forever=game.get('playtime_forever', 0) / 60
                )
                for game in raw_games if game.get('appid')
            ]
            
            print(f"✅ Encontrados {len(self.user_games)} jogos")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição HTTP: {str(e)}")
            raise
        except ValueError as e:
            print(f"❌ Erro ao processar dados: {str(e)}")
            raise
        except Exception as e:
            print(f"❌ Erro inesperado: {str(e)}")
            raise
    
    @staticmethod
    def get_game_info_steamspy(appid: int) -> Tuple[Dict, Dict]:
        """Obtém informações do jogo via SteamSpy."""
        try:
            url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
            response = requests.get(url, timeout=5).json()
            
            tags = response.get('tags', {})
            if isinstance(tags, list):
                tags = {tag: 1 for tag in tags}
                
            genres = response.get('genres', {})
            if isinstance(genres, list):
                genres = {genre: 1 for genre in genres}
                
            return tags, genres
            
        except Exception as e:
            print(f"⚠️ Erro ao buscar dados do jogo {appid}: {str(e)}")
            return {}, {}
    
    def build_user_profile(self, num_games: int = 10) -> None:
        """
        Constrói o perfil do usuário baseado nos jogos mais jogados.
        
        Args:
            num_games: Número de jogos a considerar para o perfil
        """
        print(f"\n🔄 Analisando perfil baseado nos top {num_games} jogos mais jogados...")
        
        tag_count = {}
        processed_games = 0
        
        # Ordena por tempo de jogo e pega os top N
        top_games = sorted(
            self.user_games,
            key=lambda x: x.playtime_forever,
            reverse=True
        )[:num_games]
        
        for game in top_games:
            try:
                if game.playtime_forever > 0:
                    print(f"\n📊 Analisando {game.name} ({game.playtime_forever:.1f}h jogadas)")
                    tags, genres = self.get_game_info_steamspy(game.appid)
                    
                    # Peso baseado no tempo de jogo
                    weight = 1 + (0.1 * min(game.playtime_forever, 100))
                    for tag in tags:
                        tag_count[tag] = tag_count.get(tag, 0) + weight
                        
                    processed_games += 1
                    
            except Exception as e:
                print(f"⚠️ Erro ao processar {game.name}: {str(e)}")
                continue
        
        self.user_profile = tag_count
        print(f"\n✅ Perfil construído com base em {processed_games} jogos")
        
        # Mostra as top tags do perfil
        print("\n🏷️ Top 5 tags do seu perfil:")
        sorted_tags = sorted(self.user_profile.items(), key=lambda x: x[1], reverse=True)[:5]
        for tag, weight in sorted_tags:
            print(f"   • {tag}: {weight:.2f}")
    
    def process_game(self, game: GameInfo) -> GameInfo:
        """Processa um jogo para recomendação."""
        try:
            tags, genres = self.get_game_info_steamspy(game.appid)
            
            # Normaliza os pesos das tags
            total_weight = sum(float(weight) for weight in tags.values())
            normalized_tags = {
                tag: (float(weight) / total_weight * 100) if total_weight > 0 else 0
                for tag, weight in tags.items()
            }
            
            # Calcula pontuação e matching tags
            tag_scores = []
            total_score = 0
            
            for tag, normalized_weight in normalized_tags.items():
                tag_score = self.user_profile.get(tag, 0)
                if tag_score > 0:
                    tag_scores.append({
                        'tag': tag,
                        'score': tag_score,
                        'weight': round(normalized_weight, 2)
                    })
                    total_score += tag_score
            
            game.score = total_score
            game.matching_tags = sorted(tag_scores, key=lambda x: x['score'], reverse=True)
            game.tags = normalized_tags
            game.genres = genres
            
            return game
            
        except Exception as e:
            print(f"\n❌ Erro ao processar {game.name}: {str(e)}")
            return game
    
    def recommend_games(self, max_recommendations: int = 10, max_workers: int = 10) -> List[GameInfo]:
        """
        Recomenda jogos baseado no perfil do usuário.
        
        Args:
            max_recommendations: Número máximo de jogos a recomendar
            max_workers: Número máximo de threads
        """
        if not self.user_profile:
            raise ValueError("Perfil do usuário não construído. Execute build_user_profile primeiro.")
            
        print(f"\n🚀 Iniciando análise com {max_workers} threads...")
        
        processed = 0
        total = len(self.user_games)
        lock = threading.Lock()
        
        def update_progress():
            nonlocal processed
            with lock:
                processed += 1
                progress = (processed / total) * 100
                print(f"\r⏳ Progresso: {progress:.1f}% ({processed}/{total} jogos)", end="")
        
        recommendations = []
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_game = {
                executor.submit(self.process_game, game): game 
                for game in self.user_games
            }
            
            for future in concurrent.futures.as_completed(future_to_game):
                try:
                    game = future.result()
                    if game.score > 0:
                        recommendations.append(game)
                    update_progress()
                except Exception as e:
                    print(f"\n❌ Erro: {str(e)}")
        
        execution_time = time.time() - start_time
        print(f"\n⚡ Tempo de execução: {execution_time:.2f} segundos")
        
        # Ordena e limita as recomendações
        recommendations.sort(key=lambda x: x.score, reverse=True)
        top_recommendations = recommendations[:max_recommendations]
        
        # Exibe as recomendações
        print("\n🎯 RECOMENDAÇÕES:")
        print("=" * 80)
        
        for i, game in enumerate(top_recommendations, 1):
            print(f"\n{i}. 🎮 {game.name}")
            print(f"   📊 Pontuação: {game.score:.2f}")
            
            if game.matching_tags:
                print("   🏷️ Tags relevantes:")
                for tag_info in game.matching_tags[:5]:
                    print(f"      • {tag_info['tag']}: {tag_info['score']:.2f} pontos "
                          f"(peso: {tag_info['weight']:.1f}%)")
            
            if game.genres:
                print("   🎯 Gêneros:")
                for genre, weight in list(game.genres.items())[:3]:
                    print(f"      • {genre}: {weight}%")
            
            print("   " + "-" * 40)
        
        return top_recommendations

# Exemplo de uso atualizado:
if __name__ == "__main__":
    STEAM_API_KEY = '9E61CF132D7355A5D1CB171BED5E6FDC'  # sua chave atual
    STEAM_ID = '76561198276702363'  # seu Steam ID atual
    
    try:
        print("🎮 SISTEMA DE RECOMENDAÇÃO DE JOGOS STEAM 🎮")
        print("=" * 50)
        print(f"🔑 Verificando credenciais...")
        
        if not STEAM_API_KEY or len(STEAM_API_KEY) != 32:
            raise ValueError("Chave da API Steam inválida")
            
        if not STEAM_ID or not STEAM_ID.isdigit():
            raise ValueError("Steam ID inválido")
            
        print("✅ Credenciais válidas")
        
        # Inicializa o recomendador
        recommender = SteamGameRecommender(STEAM_API_KEY, STEAM_ID)
        
        # Busca a biblioteca do usuário
        recommender.fetch_user_library()
        
        # Constrói o perfil baseado nos top 15 jogos
        recommender.build_user_profile(num_games=15)
        
        # Gera recomendações
        recommendations = recommender.recommend_games(
            max_recommendations=10,
            max_workers=20
        )
        
    except ValueError as e:
        print(f"\n❌ Erro de validação: {str(e)}")
    except Exception as e:
        print(f"\n❌ Erro fatal: {str(e)}")
