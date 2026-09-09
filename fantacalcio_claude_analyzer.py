import os
from typing import Any

from anthropic import Anthropic


class FantacalcioClaudeAnalyzer:

    def __init__(self, model: str = "claude-fable-5-1"):
        self._api_key = os.getenv("ANTHROPIC_API_KEY")
        self._model = model
        self._claude_connection = Anthropic(api_key=self._api_key) if self._api_key else None

    def _analyze_player(self, player_name: str) -> dict:
        # Returns a concise scouting summary with at most 10 lines.
        if not player_name or not player_name.strip():
            return {"ok": False, "error": "player_name is required", "player_name": player_name, "summary": ""}

        if self._claude_connection is None:
            return {
                "ok": False,
                "error": "Missing ANTHROPIC_API_KEY. Set it in the environment or pass api_key in constructor.",
                "player_name": player_name,
                "summary": "",
            }

        prompt = (
            f"Analyze football player '{player_name}'.\\n"
            "Use your built-in web search tool to gather current, reliable information before answering.\\n"
            "IMPORTANT: focus only on players currently in the Italian Serie A league.\\n"
            "First line must be exactly one of: LEAGUE_CHECK:SERIE_A or LEAGUE_CHECK:NOT_SERIE_A\\n"
            "If NOT_SERIE_A, add one short line with current team/league and stop.\\n"
            "If SERIE_A, create a practical fantasy-football scouting summary in max 10 lines (excluding LEAGUE_CHECK line).\\n"
            "Include: current role, likely minutes, strengths, weaknesses, risk factors, and fantasy outlook.\\n"
            "Be specific, concise, and avoid fluff.\\n"
            "If data is uncertain, clearly say it is an estimate."
        )

        try:
            tool_choice: Any = {"type": "auto"}
            tools: list[Any] = [{"type": "web_search_20250305"}]
            messages: list[Any] = [{"role": "user", "content": prompt}]

            message = self._claude_connection.messages.create(
                model=self._model,
                max_tokens=450,
                system="You are a football scouting assistant for fantasy football focused on Italian Serie A.",
                tool_choice=tool_choice,
                tools=tools,
                messages=messages,
            )
            text = "".join(
                block.text for block in message.content if getattr(block, "type", "") == "text"
            ).strip()

            lines = [line.strip() for line in text.splitlines() if line.strip()]

            if not lines:
                return {
                    "ok": False,
                    "error": "Empty response from Claude API",
                    "player_name": player_name,
                    "summary": "",
                }

            league_check = lines[0]
            if league_check == "LEAGUE_CHECK:NOT_SERIE_A":
                summary = "\n".join(lines[1:2]) if len(lines) > 1 else "Player not currently in Italian Serie A."
                return {
                    "ok": False,
                    "player_name": player_name,
                    "summary": summary,
                    "error": "Player not currently in Italian Serie A",
                    "model": self._model,
                }

            content_lines = lines[1:] if league_check == "LEAGUE_CHECK:SERIE_A" else lines
            summary = "\n".join(content_lines[:10])

            return {
                "ok": True,
                "player_name": player_name,
                "summary": summary,
                "league": "Serie A",
                "model": self._model,
            }
        except Exception as exc:
            return {
                "ok": False,
                "error": f"Claude API request failed: {exc}",
                "player_name": player_name,
                "summary": "",
            }
