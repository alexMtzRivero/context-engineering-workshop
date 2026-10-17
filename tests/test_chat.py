"""Pruebas del loop real de Pydantic AI, sin API key ni llamadas externas."""

import tempfile
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic_ai import ModelRetry
from pydantic_ai.messages import ModelRequest, ModelResponse, ModelMessagesTypeAdapter, TextPart, ToolCallPart, ToolReturnPart, UserPromptPart
from pydantic_ai.models.function import FunctionModel

import app as server
from chat_agent import Chat, agent, compact, context_usage, file_path, history_json, read_file, researcher, respond, summarizer
from customer_tools import CUSTOMER_TOOLS


def answer(messages, info):
    return ModelResponse(parts=[TextPart(content="Hola.")])


def summarize(messages, info):
    return ModelResponse(parts=[TextPart(content="Plan de un viaje. Pendiente confirmar horario.")])


def toggles(chat, **on):
    """Apaga los cinco toggles y enciende los indicados."""
    for name in ("disk", "all_tools", "compaction", "on_demand", "subagent"):
        setattr(chat, name, on.get(name, False))


class AgentTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.chat = Chat(folder=Path(self.temp.name), disk=True, all_tools=True, compaction=True)

    def seed_history(self):
        self.chat.history = [
            ModelRequest(parts=[UserPromptPart(content="Reserva LIMA-4829. " + "Detalle del viaje. " * 200)]),
            ModelResponse(parts=[TextPart(content="Entendido.")]),
        ]

    async def test_basic_chat_has_history_and_no_tools(self):
        toggles(self.chat)
        seen = []

        def model(messages, info):
            self.assertEqual(info.function_tools, [])
            seen.append(history_json(self.chat))
            return answer(messages, info)

        with agent.override(model=FunctionModel(model)):
            await respond(self.chat, "Hola")
            await respond(self.chat, "¿Qué dije antes?")
        self.assertIn("Hola", seen[1])
        self.assertEqual(len(self.chat.history), 4)

    async def test_file_tools_execute_in_agent_loop(self):
        toggles(self.chat, disk=True)
        calls = iter([
            ToolCallPart(tool_name="write_file", args={"name": "notes/viaje.md", "content": "Reserva LIMA-4829"}),
            ToolCallPart(tool_name="list_files", args={"keyword": "viaje"}),
            ToolCallPart(tool_name="read_file", args={"name": "notes/viaje.md"}),
        ])

        def model(messages, info):
            self.assertEqual({t.name for t in info.function_tools}, {"list_files", "read_file", "write_file"})
            call = next(calls, None)
            return ModelResponse(parts=[call]) if call else answer(messages, info)

        with agent.override(model=FunctionModel(model)):
            data = await respond(self.chat, "Guarda y lee la reserva.")
        self.assertEqual((self.chat.folder / "notes/viaje.md").read_text(), "Reserva LIMA-4829")
        self.assertIn("LIMA-4829", data["context"])

    async def test_compaction_without_reference_replaces_history(self):
        self.seed_history()
        with summarizer.override(model=FunctionModel(summarize)):
            report = await compact(self.chat, False)
        self.assertIsNone(report["reference"])
        self.assertEqual(list(self.chat.folder.iterdir()), [])
        self.assertNotIn("LIMA-4829", history_json(self.chat))
        self.assertLess(report["after_bytes"], report["before_bytes"])
        with agent.override(model=FunctionModel(answer)):
            await respond(self.chat, "Continuemos")

    async def test_reference_keeps_original_and_can_be_retrieved(self):
        self.seed_history()
        original = history_json(self.chat)
        self.chat.loaded_tools.add("write_file")
        with summarizer.override(model=FunctionModel(summarize)):
            report = await compact(self.chat, True)
        self.assertEqual((self.chat.folder / report["reference"]).read_text(), original)
        self.assertIn(report["reference"], history_json(self.chat))
        self.assertNotIn("LIMA-4829", history_json(self.chat))
        self.assertEqual(self.chat.loaded_tools, set())
        called = False

        def retrieve(messages, info):
            nonlocal called
            if not called:
                called = True
                return ModelResponse(parts=[ToolCallPart(tool_name="read_file", args={"name": report["reference"]})])
            self.assertIn("LIMA-4829", str(messages))
            return ModelResponse(parts=[TextPart(content="Reserva LIMA-4829")])

        with agent.override(model=FunctionModel(retrieve)):
            data = await respond(self.chat, "¿Cuál era el código de reserva?")
        self.assertEqual(data["reply"], "Reserva LIMA-4829")

    async def test_compaction_tool_applies_after_tool_result(self):
        self.seed_history()
        called = False

        def request_compaction(messages, info):
            nonlocal called
            if not called:
                called = True
                return ModelResponse(parts=[ToolCallPart(tool_name="compact_context", args={"with_reference": False})])
            return answer(messages, info)

        def check_summary_input(messages, info):
            text = str(messages)
            self.assertIn("tool-return", text)
            self.assertIn("Hola.", text)
            return summarize(messages, info)

        with agent.override(model=FunctionModel(request_compaction)), summarizer.override(model=FunctionModel(check_summary_input)):
            data = await respond(self.chat, "Compacta sin referencia")
        self.assertIsNotNone(data["compaction"])
        self.assertEqual(len(self.chat.history), 1)
        self.assertIsNone(self.chat.pending_compaction)

    async def test_discovery_exposes_schema_only_after_search(self):
        toggles(self.chat, on_demand=True)
        seen = []

        def model(messages, info):
            names = {t.name for t in info.function_tools}
            seen.append(names)
            if len(seen) == 1:
                return ModelResponse(parts=[ToolCallPart(tool_name="discover_tools", args={"keyword": "write_file"})])
            if len(seen) == 2:
                return ModelResponse(parts=[ToolCallPart(tool_name="write_file", args={"name": "nota.md", "content": "hola"})])
            return answer(messages, info)

        with agent.override(model=FunctionModel(model)):
            await respond(self.chat, "Guarda una nota")
        self.assertEqual(seen[0], {"discover_tools"})
        self.assertEqual(seen[1], {"discover_tools", "write_file"})
        self.assertEqual((self.chat.folder / "nota.md").read_text(), "hola")

    async def test_failed_summary_keeps_original(self):
        self.seed_history()
        original = history_json(self.chat)

        def fail(messages, info):
            raise RuntimeError("Proveedor no disponible")

        with summarizer.override(model=FunctionModel(fail)), self.assertRaises(RuntimeError):
            await compact(self.chat, True)
        self.assertEqual(history_json(self.chat), original)
        self.assertEqual(list(self.chat.folder.iterdir()), [])

    async def test_empty_chat_cannot_compact(self):
        with self.assertRaises(ValueError):
            await compact(self.chat, True)

    def test_paths_cannot_escape_workspace(self):
        with self.assertRaises(ModelRetry):
            file_path(self.chat, "../outside.txt")
        with self.assertRaises(ModelRetry):
            file_path(self.chat, "/etc/hosts")
        with self.assertRaises(ModelRetry):
            file_path(self.chat, ".")
        with tempfile.TemporaryDirectory() as outside:
            (self.chat.folder / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ModelRetry):
                file_path(self.chat, "link/secret.txt")

    def test_missing_file_is_a_tool_retry(self):
        with self.assertRaises(ModelRetry):
            read_file(SimpleNamespace(deps=self.chat), "missing.md")

    def test_context_meter_separates_categories_and_hidden_tools(self):
        self.chat.history = [
            ModelRequest(parts=[UserPromptPart(content="Resumen conservado")], metadata={"context_kind": "summary"}),
            ModelRequest(parts=[UserPromptPart(content="Resumen de la conversación anterior: esto es un mensaje normal")]),
            ModelResponse(parts=[ToolCallPart(tool_name="read_file", args={"name": "nota.md"})]),
            ModelRequest(parts=[ToolReturnPart(tool_name="read_file", content="Texto recuperado del disco " * 50)]),
            ModelResponse(parts=[TextPart(content="Respuesta actual")]),
        ]
        counts = context_usage(self.chat)
        self.assertTrue(counts["estimated"])
        self.assertTrue(all(counts["tokens"][key] > 0 for key in counts["tokens"]))
        self.assertEqual(counts["total_tokens"], sum(counts["tokens"].values()))
        self.assertGreater(counts["tokens"]["chat"], counts["tokens"]["summary"])
        self.chat.history.clear()
        toggles(self.chat)
        self.assertEqual(context_usage(self.chat)["tokens"]["tools"], 0)
        toggles(self.chat, on_demand=True)
        hidden = context_usage(self.chat)["tokens"]["tools"]
        self.chat.loaded_tools.add("read_file")
        self.assertGreater(context_usage(self.chat)["tokens"]["tools"], hidden)

    async def test_context_meter_changes_on_compaction_and_next_turn(self):
        self.seed_history()
        self.chat.history.append(ModelRequest(parts=[ToolReturnPart(tool_name="read_file", content="Documento largo " * 200)]))
        before = context_usage(self.chat)
        with summarizer.override(model=FunctionModel(summarize)):
            await compact(self.chat, True)
        after = context_usage(self.chat)
        self.assertEqual(after["tokens"]["chat"], 0)
        self.assertEqual(after["tokens"]["retrieved"], 0)
        self.assertGreater(after["tokens"]["summary"], 0)
        self.assertLess(after["total_tokens"], before["total_tokens"])
        with agent.override(model=FunctionModel(answer)):
            data = await respond(self.chat, "Mensaje nuevo")
        usage = data["context_usage"]
        self.assertGreater(usage["tokens"]["summary"], 0)
        self.assertGreater(usage["tokens"]["chat"], 0)
        self.assertEqual(usage["last_input_tokens"], self.chat.history[-1].usage.input_tokens)

    async def test_customer_catalog_is_sent_only_in_full_load_mode(self):
        seen = []

        def model(messages, info):
            seen.append({tool.name for tool in info.function_tools})
            return answer(messages, info)

        with agent.override(model=FunctionModel(model)):
            await respond(self.chat, "Hola")
            toggles(self.chat, on_demand=True)
            await respond(self.chat, "Hola otra vez")
        self.assertEqual(len(CUSTOMER_TOOLS), 80)
        self.assertEqual(len(seen[0]), 84)
        self.assertEqual(seen[1], {"discover_tools"})
        self.assertGreater(context_usage(Chat(folder=self.chat.folder, all_tools=True))["tokens"]["tools"], 20000)

    async def test_customer_tool_discovery_and_order_lookup(self):
        toggles(self.chat, on_demand=True)
        turns = 0

        def model(messages, info):
            nonlocal turns
            turns += 1
            names = {tool.name for tool in info.function_tools}
            if turns == 1:
                self.assertNotIn("get_order_status", names)
                return ModelResponse(parts=[ToolCallPart(tool_name="discover_tools", args={"keyword": "get_order_status"})])
            if turns == 2:
                self.assertIn("get_order_status", names)
                self.assertNotIn("cancel_order", names)
                return ModelResponse(parts=[ToolCallPart(tool_name="get_order_status", args={"order_id": "ORD-1001"})])
            self.assertIn("en tránsito", str(messages))
            self.assertIn("simulated", str(messages))
            return ModelResponse(parts=[TextPart(content="Pedido en tránsito.")])

        with agent.override(model=FunctionModel(model)):
            data = await respond(self.chat, "¿Dónde está mi pedido ORD-1001?")
        self.assertGreater(data["context_usage"]["tokens"]["retrieved"], 0)
        self.assertEqual(data["context_usage"]["tool_count"], 2)

    def test_context_preview_contains_only_active_tools_and_current_history(self):
        toggles(self.chat, on_demand=True)
        self.chat.history = [ModelRequest(parts=[UserPromptPart(content="Mensaje actual")]), ModelResponse(parts=[TextPart(content="Respuesta actual")])]
        before = context_usage(self.chat)
        preview = json.loads(before["next_context"])
        self.assertEqual([tool["name"] for tool in preview["tools"]], ["discover_tools"])
        self.assertEqual(preview["messages"][0]["parts"][0]["content"], "Mensaje actual")
        self.assertEqual(preview["messages"][1]["parts"][0]["content"], "Respuesta actual")
        self.assertNotIn('"timestamp"', before["next_context"])
        self.assertNotIn('"usage"', before["next_context"])
        self.assertLess(before["tokens"]["tools"], 100)
        self.chat.loaded_tools.add("get_order_status")
        after = context_usage(self.chat)
        self.assertEqual({tool["name"] for tool in json.loads(after["next_context"])["tools"]}, {"discover_tools", "get_order_status"})
        self.assertGreater(after["tokens"]["tools"], before["tokens"]["tools"])

    async def test_service_write_records_request_without_changing_demo_order(self):
        calls = iter([
            ToolCallPart(tool_name="cancel_order", args={"order_id": "ORD-1001", "reason": "Lo pedí por error"}),
            ToolCallPart(tool_name="get_order_status", args={"order_id": "ORD-1001"}),
        ])

        def model(messages, info):
            call = next(calls, None)
            return ModelResponse(parts=[call]) if call else answer(messages, info)

        with agent.override(model=FunctionModel(model)):
            data = await respond(self.chat, "Registra cancelación y consulta el estado")
        self.assertEqual(len(self.chat.service_requests), 1)
        self.assertTrue(self.chat.service_requests[0]["simulated"])
        self.assertEqual(self.chat.service_requests[0]["request_id"], "REQ-001")
        self.assertIn("en tránsito", data["context"])
        self.assertEqual(Chat(folder=self.chat.folder).service_requests, [])

    async def test_service_tool_validates_arguments_and_does_not_invent_customer(self):
        tool = next(tool for tool in CUSTOMER_TOOLS if tool.name == "change_order_quantity")
        with self.assertRaises(ModelRetry):
            tool.function(SimpleNamespace(deps=self.chat), order_id="ORD-1001", sku="SKU-001", quantity=-1)
        lookup = next(tool for tool in CUSTOMER_TOOLS if tool.name == "get_customer_profile")
        data = lookup.function(SimpleNamespace(deps=self.chat), customer_id="NO-EXISTE")
        self.assertFalse(data["found"])
        self.assertEqual(data["records"], [])

    async def delegate(self):
        """El principal delega; el sub-agente consulta un pedido y entrega su informe."""
        toggles(self.chat, subagent=True)
        main_calls, research_calls = [], []

        def main(messages, info):
            main_calls.append((messages, {tool.name for tool in info.function_tools}))
            if len(main_calls) == 1:
                return ModelResponse(parts=[ToolCallPart(tool_name="delegate_research", args={"task": "Investiga ORD-1001"})])
            return ModelResponse(parts=[TextPart(content="Tu pedido va en camino.")])

        def research(messages, info):
            research_calls.append({tool.name for tool in info.function_tools})
            if len(research_calls) == 1:
                return ModelResponse(parts=[ToolCallPart(tool_name="get_order_status", args={"order_id": "ORD-1001"})])
            return ModelResponse(parts=[TextPart(content="Informe: ORD-1001 sigue en ruta.")])

        with agent.override(model=FunctionModel(main)), researcher.override(model=FunctionModel(research)):
            data = await respond(self.chat, "Investiga mi pedido")
        return data, main_calls, research_calls

    async def test_subagent_returns_report_and_keeps_full_transcript_on_disk(self):
        data, main_calls, research_calls = await self.delegate()
        self.assertEqual(main_calls[0][1], {"delegate_research", "ask_researcher"})
        self.assertIn("get_order_status", research_calls[0])
        self.assertNotIn("cancel_order", research_calls[0])  # investigar es solo lectura
        self.assertIn("ORD-1001 sigue en ruta", str(main_calls[1][0]))
        self.assertNotIn("simulated", str(main_calls[1][0]))  # el resultado crudo no llega al principal
        run = data["subagents"][0]
        transcript = (self.chat.folder / run["transcript"]).read_text()
        self.assertIn("get_order_status", transcript)
        self.assertIn("simulated", transcript)
        self.assertEqual(run["messages"], 4)
        self.assertGreater(data["context_usage"]["tokens"]["retrieved"], 0)

    async def test_revived_subagent_answers_with_its_full_history(self):
        data, _, _ = await self.delegate()
        run_id = data["subagents"][0]["run_id"]
        calls = 0

        def main(messages, info):
            nonlocal calls
            calls += 1
            if calls == 1:
                return ModelResponse(parts=[ToolCallPart(tool_name="ask_researcher", args={"run_id": run_id, "question": "¿Qué consultaste?"})])
            return ModelResponse(parts=[TextPart(content="Consultó el estado del pedido.")])

        def remember(messages, info):
            self.assertIn("Investiga ORD-1001", str(messages))
            self.assertIn("get_order_status", str(messages))
            return ModelResponse(parts=[TextPart(content="Consulté get_order_status de ORD-1001.")])

        with agent.override(model=FunctionModel(main)), researcher.override(model=FunctionModel(remember)):
            data = await respond(self.chat, "¿Cómo llegó a esa conclusión?")
        revived = data["subagents"][0]
        self.assertTrue(revived["revived"])
        self.assertEqual(revived["run_id"], run_id)
        self.assertEqual(revived["messages"], 6)
        self.assertIn("¿Qué consultaste?", (self.chat.folder / revived["transcript"]).read_text())

    async def test_unknown_subagent_is_a_tool_retry(self):
        toggles(self.chat, subagent=True)
        ctx = SimpleNamespace(deps=self.chat)
        from chat_agent import ask_researcher
        for run_id in ["noexiste", "../x"]:
            with self.assertRaises(ModelRetry):
                await ask_researcher(ctx, run_id, "¿Qué hiciste?")


class EndpointTests(unittest.TestCase):
    def test_chat_and_compaction_routes(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(server, "ROOT", Path(folder)):
            with TestClient(server.app) as client, agent.override(model=FunctionModel(answer)), summarizer.override(model=FunctionModel(summarize)):
                started = client.post("/sessions", json={"disk": True, "all_tools": True, "compaction": True}).json()
                path = "/sessions/" + started["session_id"]
                self.assertEqual(client.post(path + "/chat", json={"message": "hola"}).status_code, 200)
                compacted = client.post(path + "/compact", json={"with_reference": True})
                self.assertEqual(compacted.status_code, 200)
                self.assertTrue(compacted.json()["compaction"]["reference"])
                self.assertEqual(client.post(path + "/chat", json={"message": "seguimos"}).status_code, 200)
                self.assertEqual(client.post(path + "/chat", json={"message": ""}).status_code, 422)
                self.assertEqual(client.post("/sessions/missing/chat", json={"message": "hola"}).status_code, 404)
                self.assertEqual(client.post("/sessions", json={"subagent": True}).status_code, 200)
                self.assertEqual(client.post("/sessions", json={"step": 3}).status_code, 422)
                base = client.post("/sessions", json={}).json()["session_id"]
                self.assertEqual(client.post(f"/sessions/{base}/compact", json={"with_reference": False}).status_code, 400)


class DatasetTests(unittest.TestCase):
    def test_dataset_is_long_and_answers_are_separate(self):
        dataset = json.loads((server.ROOT / "datasets/conversacion-larga.json").read_text())
        messages = dataset["messages"]
        self.assertTrue(dataset["synthetic"])
        self.assertEqual(len(messages), 256)
        self.assertGreater(sum(len(message["content"]) for message in messages), 100000)
        self.assertEqual([message["role"] for message in messages], ["user", "assistant"] * 128)
        self.assertNotIn("questions", dataset)
        questions = json.loads((server.ROOT / "datasets/preguntas-y-respuestas.json").read_text())
        self.assertEqual(len(questions["questions"]), 16)
        self.assertEqual(questions["dataset_id"], dataset["id"])

    def test_very_long_dataset_hides_aula_norte_among_distractors(self):
        messages = json.loads((server.ROOT / "datasets/conversacion-muy-larga.json").read_text())["messages"]
        self.assertEqual(len(messages), 256 * 8)
        starts = [message["content"] for message in messages[::256]]
        self.assertEqual(sum("Aula Norte" in start for start in starts), 1)
        self.assertIn("Aula Norte", starts[4])
        cards = [message["content"].split()[3] for message in messages
                 if message["content"].startswith("Registro la tarjeta") and "en el puesto 16." in message["content"]]
        self.assertEqual(len(set(cards)), 8)  # cada caso registra su propia tarjeta para el puesto 16
        self.assertEqual(cards[4], "DOCK-CAB-14")

    def test_loading_is_free_and_both_compaction_modes_use_the_original(self):
        fixture = (server.ROOT / "datasets/conversacion-larga.json").read_text()
        calls = []

        def summary_model(messages, info):
            calls.append(messages)
            self.assertIn("AO-2048-027", str(messages))
            self.assertIn("18 de octubre de 2026", str(messages))
            return summarize(messages, info)

        with tempfile.TemporaryDirectory() as folder, patch.object(server, "ROOT", Path(folder)):
            dataset_folder = Path(folder) / "datasets"
            dataset_folder.mkdir()
            (dataset_folder / "conversacion-larga.json").write_text(fixture)
            with TestClient(server.app) as client, summarizer.override(model=FunctionModel(summary_model)):
                for index, with_reference in enumerate([False, True]):
                    started = client.post("/sessions", json={"on_demand": True, "compaction": True, "dataset": "larga"}).json()
                    self.assertEqual(len(calls), index)  # cargar no llama al modelo
                    self.assertEqual(len(started["messages"]), 256)
                    self.assertGreater(started["context_usage"]["tokens"]["chat"], 25000)
                    workspace = Path(started["folder"])
                    self.assertEqual(list(workspace.iterdir()), [])
                    path = "/sessions/" + started["session_id"]
                    result = client.post(path + "/compact", json={"with_reference": with_reference})
                    self.assertEqual(result.status_code, 200)
                    compacted = result.json()
                    self.assertEqual(compacted["context_usage"]["tokens"]["chat"], 0)
                    self.assertGreater(compacted["context_usage"]["tokens"]["summary"], 0)
                    reference = compacted["compaction"]["reference"]
                    if with_reference:
                        archive = ModelMessagesTypeAdapter.validate_json((workspace / reference).read_bytes())
                        self.assertEqual(len(archive), 256)
                    else:
                        self.assertIsNone(reference)
                        self.assertEqual(list(workspace.iterdir()), [])
