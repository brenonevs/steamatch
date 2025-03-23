from models.user import SteamUser
from models.game import SteamGame

def main():
    try:
        print("\n🚀 INICIANDO SISTEMA DE ANÁLISE STEAM 🚀")
        print("="*50)
        
        # Criando usuários
        user1 = SteamUser(username="Breno_Bhp")
        user2 = SteamUser(steam_id="76561198085937034")
        
        # # Comparando jogos
        # user1.compare_games_with(user2, num_games=15)

        # # Comparando conquistas
        # print(f"Detalhes do usuário 1: {user1.profile_details}")
        # print(f"Detalhes do usuário 2: {user2.profile_details}")

        # # Obtendo IDs
        # print(f"ID do usuário 1: {user1.steam_id}")
        # print(f"ID do usuário 2: {user2.steam_id}")

        # # Obtendo jogos
        # print(f"Jogos do usuário 1: {user1.get_games}")
        # print(f"Jogos do usuário 2: {user2.get_games}")

        # Obtendo lista de amigos
        # print(f"Amigos do usuário 1: {user1.friends_list}")
        # print(f"Amigos do usuário 2: {user2.friends_list}")

        # Obtendo jogos recentes
        # print(f"Jogos recentes do usuário 1: {user1.recently_played_games}")
        # print(f"Jogos recentes do usuário 2: {user2.recently_played_games}")

        # Obtendo conquistas
        # print(f"Conquistas do usuário 1: {user1.badges}")
        # print(f"Conquistas do usuário 2: {user2.badges}")

        # Comparando jogos
        # user1.compare_games_with(user2, num_games=30)

       
        print(user1.steam_id)

        
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
    finally:
        print("\n👋 Finalizando programa...")
        print("="*50)

if __name__ == "__main__":
    main()