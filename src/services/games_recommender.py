import os
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple
import threading
from functools import partial
import concurrent.futures
from dataclasses import dataclass
import time
from dotenv import load_dotenv

load_dotenv()

STEAM_API_KEY = os.getenv('STEAM_API_KEY')
STEAM_ID = os.getenv('STEAM_ID')

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
    
    def __init__(self, steam_id: str):
        self.api_key = STEAM_API_KEY
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

    def suggest_games(self, top_played_games_limit: int = 15, recommendation_limit: int = 10) -> List[GameInfo]:
        """
        Generates personalized game recommendations based on user's gaming profile and preferences.
        
        Args:
            top_played_games_limit: Number of most played games to analyze for profile building
            recommendation_limit: Maximum number of games to recommend
            
        Returns:
            List of recommended games sorted by relevance score
        """
        print("\n🎮 Initializing personalized game recommendation engine...")
        
        # Fetch user's game library
        self.fetch_user_library()
        
        # Analyze user's gaming preferences
        self.build_user_profile(num_games=top_played_games_limit)
        
        # Generate tailored recommendations
        return self.recommend_games(
            max_recommendations=recommendation_limit,
            max_workers=20
        )

class SteamMarketRecommender:
    """Sistema de recomendação baseado no mercado geral da Steam."""
    
    def __init__(self):
        self.api_key = STEAM_API_KEY
        self.popular_games: List[GameInfo] = []
        
    def fetch_popular_games(self, limit: int = 100) -> None:
        """Busca jogos populares da Steam com melhor tratamento de erros e rate limiting."""
        print("\n📊 Buscando jogos populares da Steam...")
        
        try:
            # Busca jogos populares
            url = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
            params = {'key': self.api_key}
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            popular_games = data['response']['ranks'][:limit]
            print(f"\n🔄 Coletando detalhes de {len(popular_games)} jogos populares...")
            
            self.popular_games = []
            failed_games = []
            
            for rank, game in enumerate(popular_games, 1):
                try:
                    # Busca detalhes do jogo
                    app_details_url = f"https://store.steampowered.com/api/appdetails"
                    params = {
                        'appids': game['appid'],
                        'cc': 'us',
                        'l': 'en',
                        'filters': 'categories,genres,basic'
                    }
                    
                    # Adiciona delay entre requisições
                    time.sleep(1.5)  # Aumentado para 1.5 segundos
                    
                    details_response = requests.get(app_details_url, params=params, timeout=10)
                    
                    # Verifica se a resposta é válida
                    if details_response.status_code != 200:
                        print(f"\n⚠️ Erro HTTP {details_response.status_code} para jogo {game['appid']}")
                        failed_games.append(game['appid'])
                        continue
                    
                    details_data = details_response.json()
                    
                    app_id = str(game['appid'])
                    if not details_data or not details_data.get(app_id, {}).get('success'):
                        print(f"\n⚠️ Dados inválidos para jogo {game['appid']}")
                        failed_games.append(game['appid'])
                        continue
                    
                    game_data = details_data[app_id]['data']
                    
                    # Extrai e formata tags e gêneros com verificações
                    categories = []
                    genres = []
                    
                    if 'categories' in game_data:
                        categories = [
                            {'description': cat.get('description', '')}
                            for cat in game_data['categories']
                            if cat.get('description')
                        ]
                    
                    if 'genres' in game_data:
                        genres = [
                            {'description': genre.get('description', '')}
                            for genre in game_data['genres']
                            if genre.get('description')
                        ]
                    
                    # Tenta buscar dados do SteamSpy, mas não falha se não conseguir
                    try:
                        steamspy_data = self.get_steamspy_info(game['appid'])
                        steamspy_tags = [
                            {'description': tag}
                            for tag in steamspy_data.get('tags', {}).keys()
                        ]
                        categories.extend(steamspy_tags)
                    except:
                        pass
                    
                    # Cria o objeto do jogo
                    game_info = GameInfo(
                        appid=game['appid'],
                        name=game_data.get('name', f"Jogo {game['appid']}"),
                        tags=categories,
                        genres=genres
                    )
                    
                    self.popular_games.append(game_info)
                    
                    # Atualiza progresso
                    print(f"\r⏳ Progresso: {(rank/len(popular_games))*100:.1f}% "
                          f"(Sucesso: {len(self.popular_games)}, Falhas: {len(failed_games)})", end="")
                    
                except requests.exceptions.RequestException as e:
                    print(f"\n⚠️ Erro de rede ao buscar jogo {game['appid']}: {str(e)}")
                    failed_games.append(game['appid'])
                    time.sleep(2)  # Espera mais tempo em caso de erro
                    continue
                    
                except Exception as e:
                    print(f"\n⚠️ Erro ao processar jogo {game['appid']}: {str(e)}")
                    failed_games.append(game['appid'])
                    continue
            
            print(f"\n\n✅ Processo concluído:")
            print(f"   ✓ {len(self.popular_games)} jogos coletados com sucesso")
            print(f"   ✗ {len(failed_games)} jogos falharam")
            
            if failed_games:
                print("\n⚠️ IDs dos jogos que falharam:")
                print(", ".join(map(str, failed_games)))
            
        except Exception as e:
            print(f"\n❌ Erro fatal ao buscar jogos populares: {str(e)}")
            raise

    @staticmethod
    def get_steamspy_info(appid: int) -> Dict:
        """Obtém informações do SteamSpy com retry."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return response.json()
                time.sleep(1)
            except:
                if attempt < max_retries - 1:
                    time.sleep(2)
                continue
        return {}

    def recommend_by_tags(self, target_tags: List[str], max_recommendations: int = 10) -> List[GameInfo]:
        """Recomenda jogos por tags com melhor tratamento."""
        if not self.popular_games:
            raise ValueError("Nenhum jogo popular carregado")
        
        print(f"\n🎯 Buscando jogos com tags: {', '.join(target_tags)}")
        
        scored_games = []
        for game in self.popular_games:
            score = 0
            matching_tags = []
            
            # Extrai todas as descrições de tags
            game_tags = set()
            for tag in game.tags or []:
                if isinstance(tag, dict) and 'description' in tag:
                    game_tags.add(tag['description'].lower())
                elif isinstance(tag, str):
                    game_tags.add(tag.lower())
            
            # Compara com as tags alvo
            for tag in target_tags:
                if tag.lower() in game_tags:
                    score += 1
                    matching_tags.append(tag)
            
            if score > 0:
                game.score = score
                game.matching_tags = matching_tags
                scored_games.append(game)
        
        # Ordena e exibe resultados
        scored_games.sort(key=lambda x: x.score, reverse=True)
        recommendations = scored_games[:max_recommendations]
        
        self._print_recommendations(recommendations, "TAGS")
        return recommendations

    def recommend_by_genre(self, target_genre: str, max_recommendations: int = 10) -> List[GameInfo]:
        """Recomenda jogos por gênero com melhor tratamento."""
        if not self.popular_games:
            raise ValueError("Nenhum jogo popular carregado")
        
        print(f"\n🎯 Buscando jogos do gênero: {target_genre}")
        
        genre_games = []
        target_genre = target_genre.lower()
        
        for game in self.popular_games:
            game_genres = set()
            for genre in game.genres or []:
                if isinstance(genre, dict) and 'description' in genre:
                    game_genres.add(genre['description'].lower())
                elif isinstance(genre, str):
                    game_genres.add(genre.lower())
            
            if target_genre in game_genres:
                genre_games.append(game)
        
        recommendations = genre_games[:max_recommendations]
        self._print_recommendations(recommendations, f"GÊNERO {target_genre.upper()}")
        return recommendations

    def _print_recommendations(self, recommendations: List[GameInfo], type_str: str) -> None:
        """Função auxiliar para imprimir recomendações."""
        print(f"\n🎮 TOP {len(recommendations)} JOGOS POR {type_str}:")
        print("=" * 80)
        
        for i, game in enumerate(recommendations, 1):
            print(f"\n{i}. 🎮 {game.name}")
            
            if game.matching_tags:
                print(f"   📊 Tags correspondentes: {len(game.matching_tags)}")
                print(f"   🏷️ Tags: {', '.join(game.matching_tags)}")
            
            if game.genres:
                print("   🎯 Gêneros:")
                for genre in game.genres:
                    if isinstance(genre, dict):
                        print(f"      • {genre.get('description', 'N/A')}")
                    else:
                        print(f"      • {genre}")
            
            print("   " + "-" * 40)

    def suggest_games(self, game_tags: List[str] = None, game_genre: str = None, popular_games_sample_size: int = 80, results_limit: int = 10) -> List[GameInfo]:
        """
        Finds similar games based on specified tags or genre from Steam's popular games.
        
        Args:
            game_tags: Target game tags for similarity matching (optional)
            game_genre: Target game genre for similarity matching (optional)
            popular_games_sample_size: Number of popular games to analyze
            results_limit: Maximum number of similar games to return
            
        Returns:
            List of similar games sorted by relevance
        """
        print("\n🎮 Starting similarity-based game search...")
        
        # Collect current popular games data
        self.fetch_popular_games(limit=popular_games_sample_size)
        
        # Find games matching specified tags
        if game_tags:
            return self.recommend_by_tags(
                target_tags=game_tags,
                max_recommendations=results_limit
            )
        
        # Find games matching specified genre
        if game_genre:
            return self.recommend_by_genre(
                target_genre=game_genre,
                max_recommendations=results_limit
            )
            
        raise ValueError("Search criteria required: Please provide either game tags or genre")
