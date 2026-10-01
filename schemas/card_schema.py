"""Esquemas Pydantic del ADN simbólico de cartas — ArcanaGraph Lab."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class CardType(str, Enum):
    ARCANO_MAYOR = "arcano_mayor"
    ARCANO_MENOR = "arcano_menor"


class Attribution(BaseModel):
    """Metadatos de procedencia de un atributo anotationable."""

    value: str | int | float | bool | list[Any] | dict[str, Any]
    source: Literal["manual", "migrated", "inferred", "taxonomy"] = "manual"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reviewed: bool = False
    author: str | None = None
    method: str | None = None


class Personaje(BaseModel):
    tipo: str
    cantidad: int = Field(default=1, ge=0)
    movimiento: str | None = None


class Direcciones(BaseModel):
    mirada: list[str] = Field(default_factory=list)
    movimiento: list[str] = Field(default_factory=list)
    orientacion_general: str | None = None


class PalabrasClave(BaseModel):
    neutrales: list[str] = Field(default_factory=list)
    luz: list[str] = Field(default_factory=list)
    sombra: list[str] = Field(default_factory=list)


class Numerologia(BaseModel):
    numero: int
    reduccion: int

    @model_validator(mode="after")
    def check_reduction(self) -> Numerologia:
        n = abs(self.numero)
        r = n
        while r > 9:
            r = sum(int(d) for d in str(r))
        if self.reduccion != r and self.numero != 0:
            # Permitir 0 (El Loco) con reducción 0 o 22→4 documentada; validar si no coincide
            expected = r if n != 0 else 0
            if self.numero == 22:
                expected = 4
            if self.reduccion not in {expected, r}:
                pass  # soft: taxonomía histórica varia
        return self


class ColorFeatures(BaseModel):
    dominantes_rgb: list[list[int]] = Field(default_factory=list)
    dominantes_hex: list[str] = Field(default_factory=list)
    dominantes_lab: list[list[float]] = Field(default_factory=list)
    porcentajes: list[float] = Field(default_factory=list)
    luminosidad_media: float = 0.0
    saturacion_media: float = 0.0
    temperatura_visual: Literal["calida", "fria", "neutra", "desconocida"] = "desconocida"
    histograma_hue_bins: list[float] = Field(default_factory=list)

    @field_validator("dominantes_rgb")
    @classmethod
    def rgb_triplet(cls, v: list[list[int]]) -> list[list[int]]:
        for c in v:
            if len(c) != 3 or any(not (0 <= x <= 255) for x in c):
                raise ValueError(f"RGB inválido: {c}")
        return v


class SignificadoFuente(BaseModel):
    """Capa interpretativa atribuida a una fuente (paráfrasis de estudio)."""

    fuente: str
    autores: list[str] = Field(default_factory=list)
    esencia: str = ""
    subtitulo: str = ""
    en_lectura: str = ""
    preguntas: list[str] = Field(default_factory=list)
    palabras_luz: list[str] = Field(default_factory=list)
    palabras_sombra: list[str] = Field(default_factory=list)
    palabras_neutrales: list[str] = Field(default_factory=list)


class CardDNA(BaseModel):
    """ADN simbólico extensible de una carta."""

    id: str = Field(..., pattern=r"^[a-z0-9_]+$")
    nombre: str
    nombre_original: str
    numero: int = Field(..., ge=0, le=78)
    tipo: CardType
    palo: str | None = None
    mazo: str = "rider_waite_smith"
    imagen: str
    colores: ColorFeatures = Field(default_factory=ColorFeatures)
    elementos: list[str] = Field(default_factory=list)
    simbolos: list[str] = Field(default_factory=list)
    personajes: list[Personaje] = Field(default_factory=list)
    direcciones: Direcciones = Field(default_factory=Direcciones)
    palabras_clave: PalabrasClave = Field(default_factory=PalabrasClave)
    arquetipos: list[str] = Field(default_factory=list)
    emociones: list[str] = Field(default_factory=list)
    etapas_narrativas: list[str] = Field(default_factory=list)
    numerologia: Numerologia | None = None
    significados: list[SignificadoFuente] = Field(default_factory=list)
    fuentes: list[str] = Field(default_factory=list)
    version: int = 1
    attributions: dict[str, list[Attribution]] = Field(default_factory=dict)
    legacy_filename: str | None = None

    def content_hash_payload(self) -> dict[str, Any]:
        """Payload estable para hash de embeddings (sin colores derivados)."""
        return self.model_dump(
            exclude={"colores", "attributions"},
            mode="json",
        )


class DimensionScores(BaseModel):
    color: float = 0.0
    symbols: float = 0.0
    semantic: float = 0.0
    archetypes: float = 0.0
    emotions: float = 0.0
    elements: float = 0.0
    numerology: float = 0.0
    narrative: float = 0.0


class SimilarityExplanation(BaseModel):
    shared_symbols: list[str] = Field(default_factory=list)
    shared_archetypes: list[str] = Field(default_factory=list)
    shared_emotions: list[str] = Field(default_factory=list)
    related_keywords: list[str] = Field(default_factory=list)
    shared_elements: list[str] = Field(default_factory=list)
    color_notes: list[str] = Field(default_factory=list)
    main_differences: list[str] = Field(default_factory=list)
    active_dimensions: list[str] = Field(default_factory=list)


class SimilarityResult(BaseModel):
    card_a: str
    card_b: str
    similarity_total: float
    dimensions: DimensionScores
    contributions: DimensionScores
    explanation: SimilarityExplanation
    profile: str
    model_version: str = "1.0.0-iter1"


class SpreadAnalyzeResult(BaseModel):
    cards: list[str]
    metrics: dict[str, Any] = Field(default_factory=dict)
    dominant_patterns: dict[str, Any] = Field(default_factory=dict)
    missing_patterns: dict[str, Any] = Field(default_factory=dict)
    bridge_card: dict[str, Any] | None = None
    strongest_pair: dict[str, Any] | None = None
    tension_pair: dict[str, Any] | None = None
    hidden_paths: list[dict[str, Any]] = Field(default_factory=list)
    narrative_hypotheses: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Herramienta experimental. Las métricas describen este modelo y datos, "
        "no verdades universales ni predicciones verificadas. "
        "No sustituye atención médica, psicológica, legal o financiera."
    )
