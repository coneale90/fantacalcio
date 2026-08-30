import streamlit as st

from fantacalcio_core import Fantacalcio

# Use full-width layout for the app.
st.set_page_config(page_title="Conecalcio 2026", layout="wide")

default_color = ["#ADD8E6", "#90EE90"]


class FantacalcioUI:

    def __init__(self):
        self._fc = Fantacalcio()

    def _compute_player(self, player_name: str) -> dict:
        return self._fc.compute_player(player_name)

    def run(self):
        st.title("Conecalcio 2026")

        with st.form(key="player_form"):
            player_options = self._fc.all_names()
            player = st.selectbox(
                "Giocatore",
                options=player_options,
                index=None,
                placeholder="Seleziona un giocatore",
            )
            submit_button = st.form_submit_button(label="Analizza")

        if submit_button:
            if not player:
                st.warning("Seleziona un giocatore.")
            else:
                player_name = player.strip()
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

if "fantacalcio" not in st.session_state:
    st.session_state["fantacalcio"] = FantacalcioUI()
gui = st.session_state["fantacalcio"]
gui.run()
