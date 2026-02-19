import os
import shutil
from datetime import datetime
from loguru import logger
from src.config import settings
from src.extractors import extract_content
from src.ai_engine import AIEngine
from src.models import ProcessingResult, FileAnalysis
import json
from src.report import generate_report


class Pipeline:
    def __init__(self):
        self.ai_engine = AIEngine()
        self.output_dir = settings.OUTPUT_DIR
        self.input_dir = settings.INPUT_DIR
        self.results = []
        os.makedirs(self.output_dir, exist_ok=True)

    def process_filename(self, filename: str, analysis: FileAnalysis):
        ext = os.path.splitext(filename)[1]
        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_desc = "".join(c for c in analysis.description if c.isalnum() or c in " -_")
        new_filename = f"{date_str}_{analysis.category}_{safe_desc}{ext}"
        return new_filename

    def check_threshold(self, filename: str, analysis: FileAnalysis):
        if analysis.confiance < settings.CONFIDENCE_THRESHOLD:
            logger.warning(f"File {filename} is not relevant enough for categorization (confidence={analysis.confiance:.2f})")
            destination_folder = "A_verifier"
            status = "to_be_checked"
        else:
            destination_folder = analysis.category
            status = "success"
        return destination_folder, status

    def write_verifier_note(self, dest_dir: str, filename: str, analysis: FileAnalysis):
        """Écrit une note explicative quand un fichier est placé dans A_verifier/."""
        note_path = os.path.join(dest_dir, f"{os.path.splitext(filename)[0]}_note.txt")
        note = (
            f"Fichier : {filename}\n"
            f"Catégorie proposée : {analysis.category}\n"
            f"Score de confiance : {analysis.confiance:.2f} (seuil : {settings.CONFIDENCE_THRESHOLD})\n"
            f"Raisonnement : {analysis.raisonnement}\n"
            f"\nAction requise : Veuillez vérifier manuellement ce fichier et le déplacer "
            f"dans le bon dossier fanga_organised/{{categorie}}/."
        )
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(note)
        logger.info(f"Note explicative créée : {note_path}")

    def process_file(self, filename: str):
        file_path = os.path.join(self.input_dir, filename)

        try:
            text_content, is_img = extract_content(file_path)

            analysis = self.ai_engine.analyse_file(file_path, text_content, image_path=file_path if is_img else None)

            destination_folder, status = self.check_threshold(filename, analysis)

            new_filename = self.process_filename(filename, analysis)

            dest_dir = os.path.join(self.output_dir, destination_folder)
            os.makedirs(dest_dir, exist_ok=True)
            shutil.move(file_path, os.path.join(dest_dir, new_filename))

            # Créer une note explicative pour les fichiers à vérifier manuellement
            if status == "to_be_checked":
                self.write_verifier_note(dest_dir, new_filename, analysis)

            return ProcessingResult(
                original_title=filename,
                final_title=new_filename,
                category=analysis.category,
                confiance=analysis.confiance,
                status=status,
            )

        except Exception as e:
            logger.error(f"Error while processing file {filename}: {e}")
            error_dir = os.path.join(self.output_dir, "Erreurs")
            os.makedirs(error_dir, exist_ok=True)
            shutil.move(file_path, os.path.join(error_dir, filename))
            return ProcessingResult(original_title=filename, status="error", error_message=str(e))

    def process_directory(self):
        for file in os.listdir(self.input_dir):
            file_path = os.path.join(self.input_dir, file)
            result = self.process_file(file)
            self.results.append(result)

        generate_report(self.results, self.output_dir)
