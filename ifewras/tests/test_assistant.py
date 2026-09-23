"""Tests for the FloodCast AI assistant: offline NLP engine, situation tools and the Claude tool loop.
"""
import json
import os
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from starlette.testclient import TestClient
from app.main import app
from app.assistant import engine, nlp, tools
from app.scenarios.scenario_manager import scenario_manager


class TestOfflineNLP(unittest.TestCase):
    def setUp(self):
        scenario_manager.compute_hour(60)

    def test_intents_and_entities(self):
        cases = {
            "give me an overview": "overview",
            "which zones are red?": "zones",
            "how is mandia char doing": "village",
            "what's the forecast for the brahmaputra": "forecast",
            "how many boats in Barpeta": "relief",
            "have the sms been sent": "alerts",
            "what should we do next": "actions",
            "helpline numbers": "contacts",
            "is Dhubri safe?": "district",
            "बाढ़ की स्थिति क्या है": "overview",
        }
        for question, intent in cases.items():
            self.assertEqual(nlp.classify(question)[0], intent, question)
        self.assertEqual(nlp.classify("which zones are red?")[1]["level"], "RED")
        self.assertEqual(nlp.classify("status of salmora")[1]["village"], "Salmora")

    def test_answers_use_live_numbers(self):
        overview = tools.get_situation_overview()
        reply = nlp.answer("situation overview")["reply"]
        self.assertIn(f"{overview['flooded_area_sq_km']} km²", reply)
        self.assertIn(str(overview["p1_extreme_risk_villages"]), reply)

    def test_language_detection(self):
        self.assertEqual(nlp.detect_language("বানৰ পৰিস্থিতি"), "assamese")
        self.assertEqual(nlp.detect_language("बाढ़"), "hindi")
        self.assertTrue(nlp.answer("बाढ़ की स्थिति")["reply"].startswith(nlp.LOCAL_HEADLINES["hindi"]))

    def test_village_tool_fuzzy_match(self):
        self.assertEqual(tools.get_village("mandia")["village"], "Mandia Char")
        self.assertEqual(tools.get_village("Salmorra")["village"], "Salmora")
        self.assertIn("error", tools.get_village("Atlantis"))

    def test_recommended_actions(self):
        actions = tools.get_recommended_actions()["actions"]
        self.assertTrue(actions)
        self.assertTrue(any("red zone" in a for a in actions))


def _block(**kw):
    return SimpleNamespace(**kw)


class TestClaudeLoop(unittest.TestCase):
    def test_tool_use_loop_returns_final_text(self):
        scenario_manager.compute_hour(60)
        responses = [
            _block(stop_reason="tool_use", content=[
                _block(type="thinking", thinking=""),
                _block(type="tool_use", id="tu_1", name="get_zones", input={"level": "RED"}),
            ]),
            _block(stop_reason="end_turn", content=[_block(type="text", text="There are **5** red zones.")]),
        ]
        fake = mock.MagicMock()
        fake.beta.messages.create.side_effect = responses

        with mock.patch.dict(os.environ, {"ASSISTANT_MODE": "claude"}), \
                mock.patch("anthropic.Anthropic", return_value=fake):
            result = engine.chat("which zones are red?", [{"role": "assistant", "content": "hi"}])

        self.assertEqual(result["mode"], "claude")
        self.assertEqual(result["reply"], "There are **5** red zones.")
        self.assertEqual(result["tools_used"], ["get_zones"])

        second = fake.beta.messages.create.call_args_list[1].kwargs
        self.assertEqual(second["model"], engine.MODEL)
        self.assertEqual(second["fallbacks"], "default")
        tool_result = second["messages"][-1]["content"][0]
        self.assertEqual(tool_result["tool_use_id"], "tu_1")
        zones = json.loads(tool_result["content"])["zones"]
        self.assertTrue(zones and all(z["level"] == "RED" for z in zones))
        # History starting with an assistant turn is dropped; the conversation starts with the user
        self.assertEqual(second["messages"][0]["role"], "user")

    def test_falls_back_to_offline_on_api_error(self):
        import anthropic
        fake = mock.MagicMock()
        fake.beta.messages.create.side_effect = anthropic.APIConnectionError(request=mock.MagicMock())
        with mock.patch.dict(os.environ, {"ASSISTANT_MODE": "claude"}), \
                mock.patch("anthropic.Anthropic", return_value=fake):
            result = engine.chat("give me an overview")
        self.assertEqual(result["mode"], "offline")
        self.assertIn("notice", result)
        self.assertIn("red zone", result["reply"].lower())


class TestAssistantEndpoints(unittest.TestCase):
    def test_chat_endpoint_offline(self):
        with mock.patch.dict(os.environ, {"ASSISTANT_MODE": "offline"}):
            client = TestClient(app)
            self.assertEqual(client.get("/api/v1/assistant/status").json()["mode"], "offline")
            res = client.post("/api/v1/assistant/chat", json={"message": "what should we do next?", "history": []})
            self.assertEqual(res.status_code, 200)
            self.assertIn("next steps", res.json()["reply"].lower())


if __name__ == "__main__":
    unittest.main()
