from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime



CategoryType = Literal["Contrats", "Facture", "Photos", "Rapports",
    "Export_csv", "Documents_identite", "Maintenance", "Autres"]


class FileAnalysis(BaseModel):
    """Sortie de l'analyse des fichiers"""
    category: CategoryType
    file_name: str
    description : str = Field(..., description="Description concise pour le nom de fichier (ex: station-cocody)")
    confiance: float = Field(..., ge=0, le=1, description="Scrore de confiance entre 0 et 1")
    raisonnement: str = Field(..., description="Pourquoi cette catégorie ?")


class ProcessingResult(BaseModel):
    original_title: str
    final_title: Optional[str] = None
    category: Optional[CategoryType] = None
    confiance: float = 0.0
    status: Literal["success", "error", "to_be_checked"]
    error_message: Optional[str] = None

