"""A small client for the Gemini Interactions API, using only Python's standard library.

Docs: https://ai.google.dev/gemini-api/docs/interactions
Request:  POST https://generativelanguage.googleapis.com/v1beta/interactions
          header x-goog-api-key, JSON body {model, input, system_instruction, ...}
Response: an Interaction whose "steps" include a model_output step with text content.
"""

import json
import time
import urllib.error
import urllib.request

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"


class GeminiError(Exception):
    pass


def _collect_text(node, out):
    """Gather every "text" string under a node, in order."""
    if isinstance(node, dict):
        if isinstance(node.get("text"), str):
            out.append(node["text"])
        for key, value in node.items():
            if key != "text":
                _collect_text(value, out)
    elif isinstance(node, list):
        for item in node:
            _collect_text(item, out)


def extract_text(interaction):
    """Pull the model's answer out of an Interaction resource."""
    if isinstance(interaction.get("output_text"), str):
        return interaction["output_text"]
    steps = interaction.get("steps") or interaction.get("outputs") or []
    model_steps = [s for s in steps if isinstance(s, dict) and "model_output" in str(s.get("type", ""))]
    texts = []
    _collect_text(model_steps or steps, texts)
    if not texts:
        raise GeminiError("Gemini replied, but the reply had no text in it.")
    return "".join(texts)


class Gemini:
    def __init__(self, api_key, model, timeout=60):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def _body(self, system, user_input, thinking):
        return {
            "model": self.model,
            "input": user_input,
            # Models often guess their own version wrongly, so state it.
            "system_instruction": f"{system}\n\nYou are running on the Gemini model {self.model}. "
                                  "If asked which model you are, say exactly that.",
            "store": False,
            "generation_config": {"thinking_level": thinking},
        }

    def _open(self, body, stream=False):
        req = urllib.request.Request(
            ENDPOINT + ("?alt=sse" if stream else ""),
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
            method="POST",
        )
        try:
            return urllib.request.urlopen(req, timeout=self.timeout)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            if e.code in (401, 403):
                raise GeminiError("Gemini rejected the API key. Check GEMINI_API_KEY in your .env file.") from e
            if e.code == 429:
                raise GeminiError("Gemini says too many requests right now. Wait a minute and try again.") from e
            if e.code == 404:
                raise GeminiError(f"Gemini doesn't recognise the model '{self.model}'. Check GEMINI_MODEL in .env.") from e
            raise GeminiError(f"Gemini returned an error ({e.code}): {detail}") from e
        except urllib.error.URLError as e:
            raise GeminiError("Couldn't reach Gemini. Check your internet connection.") from e

    def generate(self, system, user_input, schema=None, thinking="low"):
        body = self._body(system, user_input, thinking)
        if schema:
            body["response_format"] = {"type": "text", "mime_type": "application/json", "schema": schema}
        with self._open(body) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = extract_text(data)
        if schema:
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                raise GeminiError("Gemini's reply wasn't valid JSON.") from e
        return text

    def stream(self, system, user_input, thinking="low"):
        """Yield the reply's text in pieces as Gemini writes it.

        Gemini sends server-sent events; the answer's text arrives in "step.delta"
        events whose delta has type "text". Thinking steps are skipped.
        """
        body = self._body(system, user_input, thinking)
        body["stream"] = True
        with self._open(body, stream=True) as resp:
            try:
                for raw in resp:
                    line = raw.decode("utf-8").strip()
                    if not line.startswith("data:"):
                        continue
                    try:
                        event = json.loads(line[5:])
                    except json.JSONDecodeError:
                        continue
                    if event.get("error"):
                        err = event["error"]
                        raise GeminiError(f"Gemini stopped with an error: {err.get('message', err) if isinstance(err, dict) else err}")
                    delta = event.get("delta") or {}
                    if event.get("event_type") == "step.delta" and delta.get("type") == "text" and delta.get("text"):
                        yield delta["text"]
            except OSError as e:
                raise GeminiError("Lost the connection to Gemini part way through. Try again.") from e


class FakeGemini:
    """Canned replies, for testing the app without an API key (TUTOR_FAKE_AI=1)."""

    model = "fake"

    def generate(self, system, user_input, schema=None, thinking="low"):
        if schema and "exercises" in json.dumps(schema):
            return {"exercises": [
                {
                    "title": "Double it",
                    "task": "Print the number 21 doubled, using the * operator.",
                    "file": "double.py",
                    "starter": "# Print 21 doubled\n",
                    "inputs": [],
                    "tests": ['check("Shows 42", printed(), ["42"])', 'check("Uses *", "*" in source(), True)'],
                    "solution": "print(21 * 2)",
                    "hint": "Multiply with a star: 21 * 2.",
                },
                {
                    "title": "Broken on purpose",
                    "task": "This one has a wrong test and should be filtered out.",
                    "file": "broken.py",
                    "starter": "",
                    "inputs": [],
                    "tests": ['check("Impossible", printed(), ["nope"])'],
                    "solution": "print('yes')",
                    "hint": "",
                },
            ]}
        if "MISTAKE" in user_input:
            return ("**In real life:** it's like a recipe that says \"add the eggs\" but the eggs are still in the shop.\n\n"
                    "Look at line 1. Which quote is missing?")
        return ("This is a test reply from the fake tutor. It arrives in pieces, the way Gemini streams.\n\n"
                "Here is some `code` and a list:\n- one\n- two\n\n```python\nprint(\"streamed\")\n```\n\nThe end.")

    def stream(self, system, user_input, thinking="low"):
        text = self.generate(system, user_input, thinking=thinking)
        for i in range(0, len(text), 18):
            time.sleep(0.08)
            yield text[i:i + 18]
