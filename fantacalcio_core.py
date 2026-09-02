import os
import threading
from time import sleep

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from pandas import DataFrame
from concurrent.futures import ThreadPoolExecutor


class Fantacalcio:

    def __init__(self):
        self._folder_data = './data'
        self._headers = ["Codice", "Ruolo", "Nome", "Voto", "Gol Fatti", "Gol Subiti", "Rigori Parati",
                         "Rigori Segnati", "Rigori Sbagliati", "Autorete", "Ammonizioni", "Espulsioni", "Assist",
                         "Anno", "Giornata"]

        self._numeric_columns = [
            "Voto", "Gol Fatti", "Gol Subiti", "Rigori Parati", "Rigori Segnati", "Rigori Sbagliati", "Autorete",
            "Ammonizioni", "Espulsioni", "Assist"
        ]

        self._all_year_day = set()
        self._fanta_2026 = self.process_file("fanta_2026")
        self._fanta_2025 = self.process_file("fanta_2025")
        self._fanta_2024 = self.process_file("fanta_2024")
        self._fanta_2023 = self.process_file("fanta_2023")
        self._fanta_2022 = self.process_file("fanta_2022")
        self._merged = pd.concat(
            [self._fanta_2026, self._fanta_2025, self._fanta_2024, self._fanta_2023, self._fanta_2022])
        self._votes = self.read_votes()
        self.plots: dict[str, Figure | DataFrame | None] = {
            "voteSummary": None,
            "marketSummary": None,
            "quotationChart": None,
            "marketValueChart": None,
            "voteTrendChart": None,
        }
        self._cache_plots = {}
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._executor.submit(self._compute_all_player_2026_background)
        self.lock = threading.Lock()

    def _compute_all_player_2026_background(self):
        sleep(10)
        names = self._fanta_2026["Nome"].unique().tolist()
        for n in names:
            self._executor.submit(self.compute_player, n)

    def all_names(self) -> list[str]:
        names = sorted(self._fanta_2026["Nome"].unique().tolist())
        return names

    def compute_player(self, to_analyze):
        thread_id = threading.get_ident()
        thread_name = threading.current_thread().name
        print(f"Thread {thread_id} ({thread_name}) computing {to_analyze}")
        for key in self.plots:
            self.plots[key] = None

        if to_analyze in self._cache_plots:
            with self.lock:
                plots = self._cache_plots[to_analyze]
                has_market_summary = plots is not None and "marketSummary" in plots
                if has_market_summary:
                    return plots

        games_data = self.analyze_player_games(self._votes, to_analyze)
        player_data = self.analyze_player(self._merged, to_analyze)
        all_data = {}
        all_data.update(games_data)
        all_data.update(player_data)

        with self.lock:
            self._cache_plots[to_analyze] = all_data

        return all_data

    def search_role(self, name):
        player = self.data_player(self._merged, name)
        return player["Ruolo"].unique()[0]

    def process_file(self, fanta_name):
        fanta_df = pd.read_excel(f"{self._folder_data}/{fanta_name}.xlsx", header=1)
        year = fanta_name.split("_")[1]
        fanta_df["Anno"] = year
        fanta_df.drop(columns=["Id"], inplace=True)
        return fanta_df

    def read_votes(self):
        start_with = "voti_"
        df = pd.DataFrame(columns=self._headers)
        for file in os.listdir(self._folder_data):

            if file.startswith(start_with) and file.endswith(".xlsx"):
                year = file.split("_")[1]
                day = file.split("_")[3].split(".")[0]
                votes_df = pd.read_excel(f"{self._folder_data}/{file}", sheet_name="Fantacalcio")
                self._all_year_day.add((year, day))
                for col in self._numeric_columns:
                    if col in votes_df.columns:
                        # for the column replace , with . and remove the * and force to num, then cast to float
                        votes_df[col] = pd.to_numeric(
                            votes_df[col].astype(str).str.replace(",", ".", regex=False).str.replace("*", "",
                                                                                                     regex=False),
                            errors="coerce"
                        ).astype(float)
                mask = pd.to_numeric(votes_df.iloc[:, 0], errors="coerce").notna()
                only_votes_df = votes_df[mask].copy()
                only_votes_df["Anno"] = int(year)
                only_votes_df["Giornata"] = int(day)
                only_votes_df.columns = self._headers
                df = pd.concat([df, only_votes_df], ignore_index=True)
        return df

    def data_player(self, df, search_player, role=None):
        # filer all rows where "Nome" column contains full or part of the search_player string case-insensitive
        filtered_df = df[df["Nome"].str.contains(search_player, case=False, na=False)]
        if role:
            filtered_df = filtered_df[filtered_df["Ruolo"] == role]
        return filtered_df.copy()

    def charts_market(self, df):
        columns_needed = ["Quotazione Attuale", "Quatozione Iniziale", "Fanta Valore Mercato", "Anno"]
        missing_columns = [c for c in columns_needed if c not in df.columns]

        if missing_columns:
            print(f"Cannot build charts, missing columns: {missing_columns}")
        else:
            player_history = df.copy()
            player_history["Anno"] = pd.to_numeric(player_history["Anno"], errors="coerce")
            for col in ["Quotazione Attuale", "Quatozione Iniziale", "Fanta Valore Mercato"]:
                player_history[col] = pd.to_numeric(
                    player_history[col].astype(str).str.replace(",", ".", regex=False),
                    errors="coerce"
                )
            player_history = player_history.sort_values("Anno")

            if player_history[["Quotazione Attuale", "Quatozione Iniziale", "Fanta Valore Mercato"]].isna().all().all():
                print("No chart generated: selected rows do not contain numeric values")
            else:
                # Streamlit line chart data: quotation trend by year.
                quotation_df = player_history[["Anno", "Quotazione Attuale", "Quatozione Iniziale"]].dropna(
                    subset=["Anno"]
                ).copy()
                quotation_df["Anno"] = quotation_df["Anno"].astype(int).astype(str)
                quotation_df = quotation_df.set_index("Anno")

                # Streamlit line chart data: market value trend by year.
                market_value_df = player_history[["Anno", "Fanta Valore Mercato"]].dropna(subset=["Anno"]).copy()
                market_value_df["Anno"] = market_value_df["Anno"].astype(int).astype(str)
                market_value_df = market_value_df.set_index("Anno")

                data = {
                    "quotationChart": quotation_df,
                    "marketValueChart": market_value_df
                }
                return data

    def summary_2026_market(self, df):
        player_history = df.copy()
        team_played_in = player_history["Squadra"].unique().tolist()
        player_2026 = player_history[player_history["Anno"] == "2026"]
        if player_2026.empty:
            print("No 2026 data available for the selected player")
        else:
            squadre = ", ".join(team_played_in)
            row_2026 = player_2026.iloc[0]
            quotazione_attuale_2026 = row_2026["Quotazione Attuale"]
            quotazione_iniziale_2026 = row_2026["Quatozione Iniziale"]
            fanta_valore_mercato_2026 = row_2026["Fanta Valore Mercato"]
            differenza_quotazione_2026 = quotazione_attuale_2026 - quotazione_iniziale_2026

            # Create a DataFrame for table display
            market_data = {
                "Metrica": [
                    "Squadre",
                    "Quotazione Attuale",
                    "Quotazione Iniziale",
                    "Differenza Quotazione",
                    "Fanta Valore Mercato"
                ],
                "Valore": [
                    f"{squadre}",
                    f"{quotazione_attuale_2026:.2f}",
                    f"{quotazione_iniziale_2026:.2f}",
                    f"{differenza_quotazione_2026:+.2f}",
                    f"{fanta_valore_mercato_2026:.2f}"
                ]
            }
            market_df = pd.DataFrame(market_data)
            data = {
                "marketSummary": market_df
            }
            return data

    def analyze_player(self, df, player_search, role=None):
        player_to_analyze = self.data_player(df, player_search, role)
        if len(player_to_analyze) == 0:
            print("No chart generated. player not found: " + player_search)
            return
        data = {}
        summary_data = self.summary_2026_market(player_to_analyze)
        marked_data = self.charts_market(player_to_analyze)
        data.update(summary_data)
        data.update(marked_data)
        return data

    def search_vote_player(self, df, player_search, role=None) -> DataFrame | None:
        player_votes = self.data_player(df, player_search, role)
        if len(player_votes) == 0:
            print("No votes found for the player: " + player_search)
            return None
        elif player_votes["Nome"].nunique() > 1:
            print("More than one player found. Please refine your search: " + player_search)
            return None
        player_votes = player_votes.sort_values(["Anno", "Giornata"])
        return player_votes

    def analyze_player_games(self, df, player_search, role=None):
        games: DataFrame | None = self.search_vote_player(df, player_search, role)
        if games is None:
            print("No votes found for the player: " + player_search)
            return None
        games["Voto"] = pd.to_numeric(
            games["Voto"].astype(str).str.replace(",", ".", regex=False).str.replace("*", "",
                                                                                     regex=False),
            errors="coerce"
        )
        games["Voto Fantacalcio"] = (
            games["Voto"] +
            (games["Gol Fatti"] * 3) -
            games["Gol Subiti"] -
            games["Autorete"] -
            (0.5 * games["Ammonizioni"]) +
            games["Assist"]
        ).astype(float)

        data = {
            "voteTrendChart": self.plot_votes(games),
            "voteSummary": self.player_games_summary(games)
        }
        return data

    def plot_votes(self, player_games: DataFrame):
        plot_df = player_games.copy()
        plot_df = plot_df.dropna(subset=["Anno", "Giornata"]).sort_values(["Anno", "Giornata"])

        all_slots = sorted(self._all_year_day, key=lambda value: (int(value[0]), int(value[1])))
        voto_by_slot: dict[tuple[int, int], float] = {}
        voto_finale_by_slot: dict[tuple[int, int], float] = {}

        for idx, row in plot_df.iterrows():
            if pd.notna(row["Voto"]):
                voto_by_slot[(int(row["Anno"]), int(row["Giornata"]))] = float(row["Voto"])
            if pd.notna(row["Voto Fantacalcio"]):
                voto_finale_by_slot[(int(row["Anno"]), int(row["Giornata"]))] = float(row["Voto Fantacalcio"])

        if all_slots:
            x_labels = [f"{int(year)} {int(day)}" for year, day in all_slots]
            voto_values = [voto_by_slot.get((int(year), int(day)), np.nan) for year, day in all_slots]
            voto_finale_values = [voto_finale_by_slot.get((int(year), int(day)), np.nan) for year, day in all_slots]
        else:
            x_labels = [f"{int(row['Anno'])} {int(row['Giornata'])}" for idx, row in plot_df.iterrows()]
            voto_values = [float(row["Voto"]) if pd.notna(row["Voto"]) else np.nan for idx, row in plot_df.iterrows()]
            voto_finale_values = [float(row["Voto Fantacalcio"]) if pd.notna(row["Voto Fantacalcio"]) else np.nan for
                                  idx, row in plot_df.iterrows()]

        trend_df = pd.DataFrame({"Voto": voto_values, "Voto Fantacalcio": voto_finale_values}, index=x_labels)
        return trend_df

    def player_games_summary(self, player_games: DataFrame):
        total_games = len(player_games)
        total_games_perc = round(total_games / len(self._all_year_day) * 100.0, 2)
        total_goals = player_games["Gol Fatti"].sum()
        total_assists = player_games["Assist"].sum()
        goal_received = player_games["Gol Subiti"].sum()
        player_name_local = player_games["Nome"].iloc[0]
        player_role_local = player_games["Ruolo"].iloc[0]
        vote_mean = round(player_games["Voto Fantacalcio"].mean(), 2)
        vote_min = player_games["Voto Fantacalcio"].min()
        vote_max = player_games["Voto Fantacalcio"].max()
        vote_median = player_games["Voto Fantacalcio"].median()
        vote_std = round(player_games["Voto Fantacalcio"].std(), 2)
        vote_var = round(player_games["Voto Fantacalcio"].var(), 2)
        q25 = player_games["Voto Fantacalcio"].quantile(0.25)
        q75 = player_games["Voto Fantacalcio"].quantile(0.75)
        costanza = player_games["Voto Fantacalcio"].std() / player_games["Voto Fantacalcio"].mean() if player_games[
            "Voto Fantacalcio"].mean() else 0
        above_10 = len(player_games[player_games["Voto Fantacalcio"] > 10])
        above_9 = len(player_games[player_games["Voto Fantacalcio"] > 9])
        above_8 = len(player_games[player_games["Voto Fantacalcio"] > 8])
        above_7 = len(player_games[player_games["Voto Fantacalcio"] > 7])
        above_6 = len(player_games[player_games["Voto Fantacalcio"] > 6])
        below_6 = len(player_games[player_games["Voto Fantacalcio"] < 6])

        # Create a DataFrame for table display instead of matplotlib textbox
        summary_data = {
            "Categoria": [
                "Nome", "Ruolo", "Partite Giocate", "% Partite Giocate ", "Totale Goal Fatti", "Goal Subiti",
                "Totale Assist",
                "Media Voto", "Minimo", "Massimo", "Mediana", "Deviazione standard", "Varianza",
                "Quantile 25%", "Quantile 75%", "Costanza", "Partite Sopra 10", "Partite Sopra 9",
                "Partite Sopra 8", "Partite Sopra 7", "Partite Sopra 6", "Partite Sotto 6"
            ],
            "Valore": [
                str(player_name_local), str(player_role_local), f"{total_games}/{len(self._all_year_day)}",
                str(total_games_perc), str(int(total_goals)), str(int(goal_received)), str(int(total_assists)),
                str(vote_mean), str(vote_min), str(vote_max), str(vote_median), str(vote_std), str(vote_var),
                str(q25), str(q75), str(round(costanza, 2)), str(above_10), str(above_9), str(above_8),
                str(above_7), str(above_6), str(below_6)
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        return summary_df
