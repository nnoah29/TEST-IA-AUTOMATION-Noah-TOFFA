
import os
import json
from collections import Counter
from datetime import datetime
from typing import List
from loguru import logger
from src.models import ProcessingResult


def countCategories(results: List[ProcessingResult]):

    total_files = len(results)

    # Count categories
    categories = Counter()
    for res in results:
        if res.status == "success" and res.category:
            categories[res.category] += 1
        elif res.status == "to_be_checked":
             if res.category:
                 categories[res.category] += 1
             else:
                 categories["Autre"] += 1
        elif res.status == "error":
            pass

    return categories, total_files

def process_report(results: List[ProcessingResult]):
    files_list = []
    error_list = []

    for res in results:
        if res.status == "error":
            error_list.append({
                "nom_original": res.original_title,
                "error_message": res.error_message
            })
        else:
            files_list.append({
                "nom_original": res.original_title,
                "nom_final": res.final_title,
                "categorie": res.category,
                "confiance": res.confiance,
                "statut": res.status if res.status != "to_be_checked" else "to_be_checked"
            })
    return files_list, error_list



def generate_report(results: List[ProcessingResult], output_dir: str):

    categories, total_files = countCategories(results)
    files_list, error_list = process_report(results)

    report_data = {
        "date_execution": datetime.now().isoformat(),
        "total_fichiers": total_files,
        "classes": dict(categories),
        "fichiers": files_list,
        "erreurs": error_list
    }
    
    report_path = os.path.join(output_dir, "rapport_traitement.json")
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=4, ensure_ascii=False)
        logger.info(f"Report generated at {report_path}")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")