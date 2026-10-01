"""Test reflexivo y mapas personales con arcanos mayores.

El modulo evita lecturas clinicas o predictivas: las respuestas se usan como
un juego de afinidad simbolica con las 22 cartas ya presentes en el proyecto.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from typing import Any

from core.card_repository import load_all_cards
from schemas.card_schema import CardDNA

DISCLAIMER = (
    "Juego simbolico y educativo: no diagnostica personalidad, no predice el futuro "
    "y no sustituye orientacion profesional."
)


@dataclass(frozen=True)
class QuizOption:
    id: str
    text: str
    weights: dict[str, int]


@dataclass(frozen=True)
class QuizQuestion:
    id: str
    text: str
    options: tuple[QuizOption, ...]


@dataclass(frozen=True)
class QuizResult:
    primary_id: str
    runner_up_ids: list[str]
    scores: dict[str, int]
    explanation: str
    invitation: str
    answered: int
    disclaimer: str = DISCLAIMER


@dataclass(frozen=True)
class GuideCardResult:
    card_id: str
    birthdate: date
    digit_sum: int
    index: int
    method: str
    explanation: str
    disclaimer: str = DISCLAIMER


@dataclass(frozen=True)
class PersonalSpreadPosition:
    number: int
    role: str
    card_id: str
    note: str
    highlighted: bool = False


@dataclass(frozen=True)
class PersonalSpread:
    birthdate: date
    seed: str
    positions: list[PersonalSpreadPosition]
    method: str
    disclaimer: str = DISCLAIMER


MAJOR_IDS = tuple(f"major_{i:02d}_{name}" for i, name in enumerate(
    [
        "fool",
        "magician",
        "high_priestess",
        "empress",
        "emperor",
        "hierophant",
        "lovers",
        "chariot",
        "strength",
        "hermit",
        "wheel_of_fortune",
        "justice",
        "hanged_man",
        "death",
        "temperance",
        "devil",
        "tower",
        "star",
        "moon",
        "sun",
        "judgement",
        "world",
    ]
))

QUESTIONS: tuple[QuizQuestion, ...] = (
    QuizQuestion(
        id="camino",
        text="Encuentras un sendero desconocido en el bosque. ¿Que haces primero?",
        options=(
            QuizOption("saltar", "Avanzo con curiosidad: ya vere que aparece.", {"major_00_fool": 3, "major_07_chariot": 1}),
            QuizOption("mapa", "Reviso mis herramientas y dibujo un plan rapido.", {"major_01_magician": 2, "major_04_emperor": 2}),
            QuizOption("escuchar", "Me quedo quieto escuchando el lugar.", {"major_02_high_priestess": 3, "major_09_hermit": 1}),
            QuizOption("companeros", "Busco a alguien para caminar en equipo.", {"major_06_lovers": 2, "major_03_empress": 2}),
        ),
    ),
    QuizQuestion(
        id="regalo",
        text="Te dan una caja cerrada con una nota: 'abrela cuando quieras'.",
        options=(
            QuizOption("ahora", "La abro de inmediato, sin ceremonia.", {"major_19_sun": 2, "major_00_fool": 2}),
            QuizOption("ritual", "Creo un pequeno ritual antes de abrirla.", {"major_05_hierophant": 2, "major_14_temperance": 2}),
            QuizOption("guardar", "La guardo hasta entender por que llego a mi.", {"major_02_high_priestess": 2, "major_12_hanged_man": 2}),
            QuizOption("probar", "La uso como pieza para inventar algo nuevo.", {"major_01_magician": 2, "major_17_star": 2}),
        ),
    ),
    QuizQuestion(
        id="conflicto",
        text="Dos amistades discuten y ambas te piden opinion.",
        options=(
            QuizOption("mediar", "Intento traducir lo que cada una quiso decir.", {"major_14_temperance": 3, "major_11_justice": 1}),
            QuizOption("limites", "Pongo reglas claras para que nadie se lastime.", {"major_04_emperor": 2, "major_11_justice": 2}),
            QuizOption("corazon", "Pregunto que necesita cuidar el vinculo.", {"major_06_lovers": 2, "major_03_empress": 2}),
            QuizOption("retirada", "Tomo distancia para ver el patron completo.", {"major_09_hermit": 2, "major_12_hanged_man": 2}),
        ),
    ),
    QuizQuestion(
        id="tormenta",
        text="Una tormenta cambia todos tus planes del dia.",
        options=(
            QuizOption("adaptar", "Reordeno la ruta y sigo moviendome.", {"major_10_wheel_of_fortune": 2, "major_07_chariot": 2}),
            QuizOption("refugio", "Hago del refugio un lugar comodo.", {"major_03_empress": 2, "major_19_sun": 1, "major_14_temperance": 1}),
            QuizOption("derribar", "Acepto que el plan viejo ya cayo.", {"major_16_tower": 3, "major_13_death": 1}),
            QuizOption("mirar", "Observo que revela la interrupcion.", {"major_18_moon": 2, "major_09_hermit": 2}),
        ),
    ),
    QuizQuestion(
        id="energia",
        text="Cuando tienes mucha energia, suele salir como...",
        options=(
            QuizOption("accion", "Direccion, velocidad y ganas de conquistar la cuesta.", {"major_07_chariot": 3, "major_08_strength": 1}),
            QuizOption("cuidado", "Cocinar, ordenar, abrazar o embellecer algo.", {"major_03_empress": 3, "major_14_temperance": 1}),
            QuizOption("brillo", "Juego, risa y ganas de compartir luz.", {"major_19_sun": 3, "major_17_star": 1}),
            QuizOption("intensidad", "Deseo, magnetismo y preguntas incomodas.", {"major_15_devil": 3, "major_18_moon": 1}),
        ),
    ),
    QuizQuestion(
        id="misterio",
        text="En un pueblo aparece una puerta que antes no estaba.",
        options=(
            QuizOption("entrar", "Entro: algunas respuestas se encuentran caminando.", {"major_00_fool": 2, "major_13_death": 2}),
            QuizOption("archivo", "Busco mapas, historias y reglas antiguas.", {"major_05_hierophant": 2, "major_20_judgement": 2}),
            QuizOption("sueno", "Espero a sonar con ella antes de tocarla.", {"major_18_moon": 3, "major_02_high_priestess": 1}),
            QuizOption("senales", "Miro si la puerta apunta a una esperanza colectiva.", {"major_17_star": 3, "major_21_world": 1}),
        ),
    ),
    QuizQuestion(
        id="reto",
        text="Tu equipo se queda sin recursos a mitad de una aventura.",
        options=(
            QuizOption("inventar", "Improviso con lo que queda sobre la mesa.", {"major_01_magician": 3, "major_10_wheel_of_fortune": 1}),
            QuizOption("resistir", "Sostengo el animo y dosifico fuerzas.", {"major_08_strength": 3, "major_14_temperance": 1}),
            QuizOption("renunciar", "Suelto lo que pesa para continuar mas livianos.", {"major_13_death": 2, "major_12_hanged_man": 2}),
            QuizOption("pedir", "Pido ayuda y reconozco que no todo se gana a solas.", {"major_20_judgement": 2, "major_21_world": 2}),
        ),
    ),
    QuizQuestion(
        id="decision",
        text="Debes elegir entre dos caminos igualmente valiosos.",
        options=(
            QuizOption("balanza", "Hago una lista honesta de consecuencias.", {"major_11_justice": 3, "major_04_emperor": 1}),
            QuizOption("deseo", "Escucho cual camino despierta mas vida.", {"major_06_lovers": 3, "major_15_devil": 1}),
            QuizOption("pausa", "Aplazo la eleccion hasta verla desde otro angulo.", {"major_12_hanged_man": 3, "major_02_high_priestess": 1}),
            QuizOption("ciclo", "Acepto que elegir tambien abre un ciclo nuevo.", {"major_10_wheel_of_fortune": 2, "major_21_world": 2}),
        ),
    ),
    QuizQuestion(
        id="sombra",
        text="Cuando algo te incomoda de ti, tu primer impulso es...",
        options=(
            QuizOption("nombrar", "Nombrarlo con precision para entenderlo.", {"major_11_justice": 2, "major_09_hermit": 2}),
            QuizOption("transformar", "Convertirlo en combustible creativo.", {"major_15_devil": 2, "major_13_death": 2}),
            QuizOption("derribo", "Dejar que rompa una estructura que ya no servia.", {"major_16_tower": 3, "major_20_judgement": 1}),
            QuizOption("suavizar", "Tratarlo con ternura hasta que baje la defensa.", {"major_08_strength": 3, "major_03_empress": 1}),
        ),
    ),
    QuizQuestion(
        id="fiesta",
        text="En una fiesta rara donde no conoces a nadie...",
        options=(
            QuizOption("centro", "Encuentro rapido una conversacion y la enciendo.", {"major_19_sun": 2, "major_01_magician": 2}),
            QuizOption("esquina", "Observo desde una esquina hasta captar el clima.", {"major_09_hermit": 2, "major_18_moon": 2}),
            QuizOption("red", "Presento personas que podrian llevarse bien.", {"major_06_lovers": 2, "major_21_world": 2}),
            QuizOption("codigo", "Aprendo el codigo del lugar: costumbres, musica, gestos.", {"major_05_hierophant": 2, "major_02_high_priestess": 2}),
        ),
    ),
    QuizQuestion(
        id="despertar",
        text="Una manana despiertas con una idea que podria cambiar tu rutina.",
        options=(
            QuizOption("llamada", "La tomo como llamada y hago el primer gesto hoy.", {"major_20_judgement": 3, "major_07_chariot": 1}),
            QuizOption("estrella", "La comparto como una vision que puede inspirar.", {"major_17_star": 3, "major_19_sun": 1}),
            QuizOption("mundo", "La conecto con un proyecto mas grande.", {"major_21_world": 3, "major_04_emperor": 1}),
            QuizOption("templanza", "La mezclo poco a poco con lo que ya existe.", {"major_14_temperance": 3, "major_10_wheel_of_fortune": 1}),
        ),
    ),
    QuizQuestion(
        id="final",
        text="Al final de una aventura, lo que mas te importa es...",
        options=(
            QuizOption("aprendizaje", "Entender que version de mi aparecio en el viaje.", {"major_20_judgement": 2, "major_09_hermit": 2}),
            QuizOption("obra", "Ver algo concreto construido con mis manos.", {"major_04_emperor": 2, "major_01_magician": 2}),
            QuizOption("vinculo", "Que los lazos hayan quedado mas vivos.", {"major_06_lovers": 2, "major_03_empress": 2}),
            QuizOption("cierre", "Sentir que el ciclo completo encontro su forma.", {"major_21_world": 3, "major_13_death": 1}),
        ),
    ),
)

SPREAD_ROLES: tuple[str, ...] = (
    "Chispa inicial",
    "Herramienta disponible",
    "Umbral intuitivo",
    "Forma de cuidar",
    "Estructura y limites",
    "Tradicion o aprendizaje",
    "Vinculos y elecciones",
    "Movimiento y voluntad",
    "Fuerza amable",
    "Lampara interior",
    "Rueda de cambios",
    "Balanza personal",
    "Nueva perspectiva",
    "Cierre que libera",
    "Mezcla y templanza",
    "Deseo y sombra vital",
    "Estructura que se abre",
    "Esperanza practicable",
    "Misterio y suenos",
    "Alegria visible",
    "Llamado a despertar",
    "Integracion del mundo",
)


def _major_cards(cards: list[CardDNA] | None = None) -> list[CardDNA]:
    selected = [c for c in (cards or load_all_cards()) if c.tipo.value == "arcano_mayor" and 0 <= c.numero <= 21]
    return sorted(selected, key=lambda c: c.numero)


def _card_lookup(cards: list[CardDNA] | None = None) -> dict[str, CardDNA]:
    return {c.id: c for c in _major_cards(cards)}


def _study_blurb(card: CardDNA) -> str:
    for item in card.significados:
        if item.esencia:
            return item.esencia
    words = card.palabras_clave.luz or card.palabras_clave.neutrales or [card.nombre]
    return ", ".join(words[:3])


def _invitation(card: CardDNA) -> str:
    if card.significados:
        for item in card.significados:
            if item.preguntas:
                return f"Esta carta te invita a preguntarte: {item.preguntas[0]}"
    words = card.palabras_clave.luz or card.arquetipos or ["mirar tu camino con calma"]
    return f"Esta carta te invita a explorar {', '.join(words[:2])}."


def score_quiz(answers: dict[str, str], cards: list[CardDNA] | None = None) -> QuizResult:
    """Puntua respuestas de forma determinista y devuelve carta principal.

    ``answers`` usa ids de pregunta como claves e ids de opcion como valores.
    Las opciones suman puntos directamente a cartas mayores; los empates se
    resuelven por numero de arcano para que el resultado sea estable.
    """
    catalog = _card_lookup(cards)
    scores = {card_id: 0 for card_id in catalog}
    answered = 0

    for question in QUESTIONS:
        option_id = answers.get(question.id)
        option = next((o for o in question.options if o.id == option_id), None)
        if option is None:
            continue
        answered += 1
        for card_id, points in option.weights.items():
            if card_id in scores:
                scores[card_id] += points

    ranked = sorted(scores.items(), key=lambda item: (-item[1], catalog[item[0]].numero, item[0]))
    primary_id = ranked[0][0]
    runner_up_ids = [card_id for card_id, value in ranked[1:4] if value > 0]
    primary = catalog[primary_id]
    explanation = (
        f"Tus respuestas se acercan a {primary.nombre}: {_study_blurb(primary)} "
        "Tomalo como un espejo ludico, no como etiqueta fija."
    )
    return QuizResult(
        primary_id=primary_id,
        runner_up_ids=runner_up_ids,
        scores=scores,
        explanation=explanation,
        invitation=_invitation(primary),
        answered=answered,
    )


def birthdate_digit_sum(birthdate: date) -> int:
    """Suma los digitos de AAAAMMDD; conserva el total antes del modulo."""
    return sum(int(char) for char in birthdate.strftime("%Y%m%d"))


def guide_card_from_birthdate(birthdate: date, cards: list[CardDNA] | None = None) -> GuideCardResult:
    """Carta guia por suma de digitos modulo 22, con El Loco como indice 0."""
    majors = _major_cards(cards)
    digit_sum = birthdate_digit_sum(birthdate)
    index = digit_sum % len(majors)
    card = majors[index]
    method = "Suma de digitos de AAAAMMDD y reduccion por modulo 22 (El Loco = 0)."
    explanation = (
        f"{birthdate.strftime('%d/%m/%Y')} suma {digit_sum}; {digit_sum} mod 22 = {index}. "
        f"Por eso la carta guia es {card.nombre}."
    )
    return GuideCardResult(
        card_id=card.id,
        birthdate=birthdate,
        digit_sum=digit_sum,
        index=index,
        method=method,
        explanation=explanation,
    )


def _spread_seed(birthdate: date, quiz_card_id: str | None = None) -> str:
    modifier = quiz_card_id or "sin-test"
    return f"{birthdate.isoformat()}|{modifier}|tejido-arcano-v1"


def personal_spread_from_birthdate(
    birthdate: date,
    cards: list[CardDNA] | None = None,
    quiz_card_id: str | None = None,
) -> PersonalSpread:
    """Ordena los 22 mayores con hashes estables derivados de fecha y test.

    No es una tirada aleatoria: la misma fecha y el mismo modificador devuelven
    siempre el mismo mapa. El resultado asigna todos los arcanos a 22 roles
    reflexivos, como un recorrido educativo por el mazo.
    """
    majors = _major_cards(cards)
    seed = _spread_seed(birthdate, quiz_card_id)
    ordered = sorted(
        majors,
        key=lambda card: hashlib.sha256(f"{seed}|{card.id}".encode("utf-8")).hexdigest(),
    )
    positions = [
        PersonalSpreadPosition(
            number=i + 1,
            role=role,
            card_id=card.id,
            note=_position_note(card, role, highlighted=card.id == quiz_card_id),
            highlighted=card.id == quiz_card_id,
        )
        for i, (role, card) in enumerate(zip(SPREAD_ROLES, ordered, strict=True))
    ]
    method = (
        "Permutacion determinista de los 22 mayores con SHA-256 usando fecha de nacimiento "
        "y, si existe, la carta del test como modificador."
    )
    return PersonalSpread(birthdate=birthdate, seed=seed, positions=positions, method=method)


def _position_note(card: CardDNA, role: str, highlighted: bool = False) -> str:
    words = card.palabras_clave.luz or card.palabras_clave.neutrales or card.arquetipos
    essence = _study_blurb(card)
    prefix = "Carta del test: " if highlighted else ""
    if words:
        return f"{prefix}{role} dialoga con {card.nombre}: {', '.join(words[:3])}. {essence}"
    return f"{prefix}{role} dialoga con {card.nombre}. {essence}"


def quiz_status() -> dict[str, Any]:
    return {
        "questions": len(QUESTIONS),
        "cards": len(MAJOR_IDS),
        "focus": "afinidad simbolica con arcanos mayores",
        "disclaimer": DISCLAIMER,
    }
