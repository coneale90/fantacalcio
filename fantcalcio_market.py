import pandas as pd


class FantacalcioMarket:

    def __init__(self):
        self._credit = 500
        self._my_game: dict[str, list[dict[str, str | float]]] = {
            'all_players': [],
            'portieri': [],
            'difensori': [],
            'centrocampisti': [],
            'attacanti': [],
        }

    def get_total_credit(self) -> int:
        return self._credit

    def set_total_credit(self, credit: int):
        self._credit = credit
        return self._credit

    def add_player(self, player: dict[str, str | float], role: str) -> bool:
        if self._credit < int(player['price']):
            return False
        self._my_game['all_players'].append(player)
        if role == 'P':
            self._my_game['portieri'].append(player)
        elif role == 'D':
            self._my_game['difensori'].append(player)
        elif role == 'C':
            self._my_game['centrocampisti'].append(player)
        elif role == 'A':
            self._my_game['attacanti'].append(player)
        return True

    def check_player_exists(self, player_name: str) -> bool:
        return any(p['name'] == player_name for p in self._my_game['all_players'])

    def remove_player(self, name: str) -> bool:

        self._my_game['all_players'] = [p for p in self._my_game['all_players'] if p['name'] != name]
        self._my_game['portieri'] = [p for p in self._my_game['portieri'] if p['name'] != name]
        self._my_game['difensori'] = [p for p in self._my_game['difensori'] if p['name'] != name]
        self._my_game['centrocampisti'] = [p for p in self._my_game['centrocampisti'] if p['name'] != name]
        self._my_game['attacanti'] = [p for p in self._my_game['attacanti'] if p['name'] != name]
        return True

    def get_current_credit(self) -> int:
        spent_credit = sum(int(p['price']) for p in self._my_game['all_players'])
        return self._credit - spent_credit

    def get_player_list_by_group(self, player_group: str):
        return self._my_game[player_group]

    def download(self):
        data = []
        for p in self._my_game['all_players']:
            data.append([p['name'], p['price'], str(p['ruolo']).upper()])
        df = pd.DataFrame(data)
        df.columns = ["Nome", "Prezzo", "Ruolo"]
        return df.to_csv().encode("utf-8")

    def read_csv_fanta(self, file):
        df = pd.read_csv(file)
        for _, row in df.iterrows():
            name = str(row["Nome"])
            price = int(row["Prezzo"])
            role = str(row["Ruolo"]).upper()
            to_add = {'name': name, 'price': price, 'ruolo': role}
            self._my_game['all_players'].append(to_add)
            if role == 'P':
                self._my_game['portieri'].append(to_add)
            if role == 'D':
                self._my_game['difensori'].append(to_add)
            if role == 'C':
                self._my_game['centrocampisti'].append(to_add)
            if role == 'A':
                self._my_game['attacanti'].append(to_add)
