import datetime as dt

import pandas as pd
import streamlit as st

from fantacalcio_core import Fantacalcio
from fantcalcio_market import FantacalcioMarket

# Use full-width layout for the app.
st.set_page_config(page_title="Conecalcio 2026", layout="wide")

default_color = ["#ADD8E6", "#90EE90"]


class FantacalcioUI:

    def __init__(self):
        self._fc = Fantacalcio()
        self._player_options = self._fc.all_names()
        self._market = FantacalcioMarket()
        self._player = ''
        if "input_price" not in st.session_state:
            st.session_state.input_price = 0.0
        if "reset_input_price" not in st.session_state:
            st.session_state.reset_input_price = False

    def _compute_player(self, player_name: str) -> dict:
        return self._fc.compute_player(player_name)

    def run(self):
        st.title("Conecalcio 2026")
        st.markdown("## Il mio gioco")
        self._action_buttons_section()
        self._credits_section()
        self._market_section()
        self._charts_and_stats()

    def _action_buttons_section(self):
        now = dt.datetime.now()
        name_file = f"fanta_2026_{now.strftime('%Y_%m_%d_%H_%S')}.csv"
        (button_col_1, button_col_2, button_col_3, spacer) = st.columns([1, 3, 3, 15])
        with button_col_1:
            settings_button = st.button("", icon=":material/settings:", icon_position="left")
            if settings_button:
                self._open_settings_dialog()
        with button_col_2:
            st.download_button(
                label="Download",
                data=self._market.download,
                file_name=name_file,
                mime="text/csv",
                icon=":material/download:",
            )
        with button_col_3:
            upload_button = st.button("Importa", icon=":material/upload_2:", icon_position="left")
            if upload_button:
                self._import()

    def _credits_section(self):
        st.write(f"Crediti Iniziali: {self._market.get_total_credit()}")
        st.write(f"Crediti Rimanenti: {self._market.get_current_credit()}")

        if st.session_state.reset_input_price:
            st.session_state.input_price = 0.0
            st.session_state.reset_input_price = False

    def _market_section(self):
        with st.form(key="buy_form"):
            (form_col_1, form_col_2) = st.columns(2)
            with form_col_1:
                player = st.selectbox(
                    "Giocatore",
                    options=self._player_options,
                    index=None,
                    placeholder="Seleziona un giocatore",
                )
            with form_col_2:
                price = st.number_input("Prezzo", key="input_price", min_value=1, step=1)

            (button_col_1, button_col_2, button_col_3, spacer) = st.columns([1, 1, 1, 10])
            with button_col_1:
                analysis_button = st.form_submit_button(label="Analizza")
            with button_col_2:
                buy_button = st.form_submit_button(label="Compra")
            with button_col_3:
                sell_button = st.form_submit_button(label="Vendi")

            if buy_button and player is not None and price is not None and price > 0:
                name = str(player)
                role = str(self._fc.search_role(name)).upper()
                already_exists = self._market.check_player_exists(name)
                if not already_exists:
                    to_add = {'name': name, 'price': int(price), 'ruolo': role}
                    self._market.add_player(to_add, role)
                    st.session_state.reset_input_price = True
                    st.rerun()
            if analysis_button:
                self._player = str(player)
            if sell_button and player is not None:
                name = str(player)
                self._market.remove_player(name)
                st.session_state.reset_input_price = True
                st.rerun()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            show_goakeeper_button = st.button("👁️", key="show_goalkeeper")
            if show_goakeeper_button:
                self._open_dialog_with_best_players_by_group('P', limit=40)
            st.markdown("#### Portieri")
            self._write_Table(self._market.get_player_list_by_group('portieri'))
        with col2:
            show_defender_button = st.button("👁️", key="show_defender")
            if show_defender_button:
                self._open_dialog_with_best_players_by_group('D', limit=70)
            st.markdown("#### Difensori")
            self._write_Table(self._market.get_player_list_by_group('difensori'))
        with col3:
            show_center_button = st.button("👁️", key="show_center")
            if show_center_button:
                self._open_dialog_with_best_players_by_group('C', limit=70)
            st.markdown("#### Centrocampisti")
            self._write_Table(self._market.get_player_list_by_group('centrocampisti'))
        with col4:
            show_attacker_button = st.button("👁️", key="show_attacker")
            if show_attacker_button:
                self._open_dialog_with_best_players_by_group('A', limit=70)
            st.markdown("#### Attacanti")
            self._write_Table(self._market.get_player_list_by_group('attacanti'))

    @st.dialog("BestPlayers", width="large")
    def _open_dialog_with_best_players_by_group(self, group, limit=30):
        players_df = self._fc.get_best_possible_player_by_role(group, limit, avg_vote_threshold=4.5)
        st.subheader(f"Top {limit} Giocatori per Ruolo: {group}")
        st.dataframe(players_df)

    @st.dialog("BestPlayers", width="large")
    def _open_settings_dialog(self, ):
        st.subheader("Impostazioni")
        total_credit = st.number_input(
            "Credito Totale",
            min_value=1,
            step=1,
            value=self._market.get_total_credit(),
            key="total_credit_input",
        )
        if st.button("Salva") and total_credit is not None:
            self._market.set_total_credit(int(total_credit))
            st.success("Impostazioni salvate con successo!")
            st.rerun()

    def _write_Table(self, players):
        if len(players) == 0:
            return
        p_df = pd.DataFrame(players)
        p_df.columns = ["Nome", "Costo", "Ruolo"]
        st.table(p_df)

    def _charts_and_stats(self):

        if self._player and len(self._player) > 3:
            player_name = self._player.strip()
            plots = {}
            with st.spinner("Analisi in corso..."):
                plots = self._compute_player(player_name)

            shown_any_plot = False
            vote_summary = plots.get("voteSummary")
            market_summary = plots.get("marketSummary")

            # Show the two summary tables side by side when both are available.
            if vote_summary is not None and market_summary is not None:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Statistiche Giocatore")
                    st.table(vote_summary)
                with col2:
                    st.subheader("Riepilogo Mercato 2026")
                    st.table(market_summary)
                shown_any_plot = True

            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                chart_data = plots.get("quotationChart")
                if chart_data is not None:
                    st.line_chart(chart_data, color=default_color)
                    shown_any_plot = True
                else:
                    st.write("Not Available")
            with col_chart2:
                chart_data = plots.get("marketValueChart")
                if chart_data is not None:
                    st.line_chart(chart_data, color=[default_color[0]])
                    shown_any_plot = True
                else:
                    st.write("Not Available")

            chart_data = plots.get("voteTrendChart")
            if chart_data is not None:
                st.line_chart(chart_data, color=default_color)
                shown_any_plot = True

            if not shown_any_plot:
                st.info("Nessun grafico disponibile per questo giocatore.")

    @st.dialog("Import")
    def _import(self):
        st.subheader("Importa Fantacalcio")
        file = st.file_uploader("Importa Fantacalcio", type="csv")
        if st.button("Upload"):
            if file is not None:
                self._market.read_csv_fanta(file)
                st.success("Fantacalcio importato con successo!")
                st.rerun()


if "fantacalcio" not in st.session_state:
    st.session_state["fantacalcio"] = FantacalcioUI()
gui = st.session_state["fantacalcio"]
gui.run()
