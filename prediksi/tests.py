import json
from unittest.mock import patch

from django.test import SimpleTestCase

from .views import panggil_api_ai


class PanggilApiAiTests(SimpleTestCase):
    @patch("prediksi.views.urllib.request.urlopen")
    def test_groq_uses_current_model_and_completion_token_parameter(self, mock_urlopen):
        response = mock_urlopen.return_value.__enter__.return_value
        response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Analisis harga kos."}}],
        }).encode("utf-8")

        result = panggil_api_ai("groq", "test-api-key", "Periksa harga kos.")

        request = mock_urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(result, "Analisis harga kos.")
        self.assertEqual(payload["model"], "openai/gpt-oss-20b")
        self.assertEqual(payload["max_completion_tokens"], 220)
        self.assertNotIn("max_tokens", payload)
