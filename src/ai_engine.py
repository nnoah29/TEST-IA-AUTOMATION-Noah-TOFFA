
import base64
import os
from abc import ABC, abstractmethod
from PIL import Image

from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
from src.config import settings
from src.models import FileAnalysis


class BaseAIEngine(ABC):
    @abstractmethod
    def analyse_file(self, file_path: str, text_content: str = None, image_path: str = None) -> FileAnalysis:
        ...

class OpenAIEngine(BaseAIEngine):
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def analyse_file(self, file_path: str, text_content: str = None, image_path: str = None) -> FileAnalysis:
        messages = [
            {"role": "system", "content": (
                "Tu es un assistant administratif expert pour FANGA, société de mobilité électrique.\n"
                "Classe chaque fichier dans UNE des catégories suivantes :\n"
                "- Contrats : contrats, accords, conventions, bons de commande\n"
                "- Facture : factures, reçus, notes de frais\n"
                "- Photos : photos terrain, véhicules, stations (hors bugs)\n"
                "- Rapports : rapports, bilans, analyses, plannings équipe\n"
                "- Export_csv : exports de données, fichiers CSV/Excel de transactions\n"
                "- Documents_identite : CNI, passeports, permis, documents RH\n"
                "- Maintenance : bugs applicatifs, captures d'écran d'erreurs, pannes, réparations, entretien matériel/flotte\n"
                "- Autres : tout ce qui ne rentre dans aucune catégorie ci-dessus"
            )}
        ]

        user_content = [
            {
                "type": "text",
                "text": f"Analyser le fichier {file_path}"
            }
        ]

        if text_content:
            user_content.append({"type": "text", "text": f"Contenu extrait du fichier:\n{text_content[:1000]}"})

        if image_path:
            ext = os.path.splitext(image_path)[1].lower().lstrip(".")
            mime_type = "jpeg" if ext == "jpg" else ext
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/{mime_type};base64,{b64}"}
            })

        messages.append({"role": "user", "content": user_content})

        completion = self.client.beta.chat.completions.parse(
            model=settings.MODEL_NAME,
            messages=messages,
            response_format=FileAnalysis,
        )
        return completion.choices[0].message.parsed



class GeminiEngine(BaseAIEngine):
    def __init__(self):
        from google import genai
        from google.genai import types
        self.genai = genai
        self.types = types
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def analyse_file(self, file_path: str, text_content: str = None, image_path: str = None) -> FileAnalysis:
        system_prompt = (
            "Tu es un assistant administratif expert pour FANGA, société de mobilité électrique.\n"
            "Classe chaque fichier dans UNE des catégories suivantes :\n"
            "- Contrats : contrats, accords, conventions, bons de commande\n"
            "- Facture : factures, reçus, notes de frais\n"
            "- Photos : photos terrain, véhicules, stations (hors bugs)\n"
            "- Rapports : rapports, bilans, analyses, plannings équipe\n"
            "- Export_csv : exports de données, fichiers CSV/Excel de transactions\n"
            "- Documents_identite : CNI, passeports, permis, documents RH\n"
            "- Maintenance : bugs applicatifs, captures d'écran d'erreurs, pannes, réparations, entretien matériel/flotte\n"
            "- Autres : tout ce qui ne rentre dans aucune catégorie ci-dessus"
        )

        prompt_parts = [f"Analyser le fichier: {file_path}"]
        if text_content:
            prompt_parts.append(f"Contenu extrait:\n{text_content[:2000]}")

        contents = []
        if image_path:
            img = Image.open(image_path)
            contents.append(img)
        contents.append("\n\n".join(prompt_parts))

        response = self.client.models.generate_content(
            model=settings.MODEL_NAME,
            contents=contents,
            config=self.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=FileAnalysis,
            )
        )

        return FileAnalysis.model_validate_json(response.text)



def build_ai_engine() -> BaseAIEngine:
    provider = settings.AI_PROVIDER.lower()
    if provider == "openai":
        logger.info("Using OpenAI engine")
        return OpenAIEngine()
    elif provider == "gemini":
        logger.info("Using Gemini engine")
        return GeminiEngine()
    else:
        raise ValueError(f"Unknown AI_PROVIDER: '{provider}'. Use 'openai' or 'gemini'.")


class AIEngine:
    def __init__(self):
        self._engine = build_ai_engine()

    def analyse_file(self, file_path: str, text_content: str = None, image_path: str = None) -> FileAnalysis:
        return self._engine.analyse_file(file_path, text_content, image_path)
