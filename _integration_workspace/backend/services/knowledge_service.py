from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENT_DIR = BASE_DIR / "genai_documents"

# ---------- Document filenames ----------

GENERAL_GUIDE = "How To Keep Your Heart Healthy The Essential Dos and Donts.txt"
DIET_GUIDE = "Heart Health Basic Dietary Guidelines.txt"
CHOLESTEROL_GUIDE = "Cholesterol and Heart Disease.txt"
BP_GUIDE = "High Blood Pressure Healthy Eating Guide.txt"
SMOKING_GUIDE = "Alcohol and Smoking.txt"

# ---------- Cache ----------

DOCUMENT_CACHE: dict[str, str] = {}


def _load_documents():
    """Load all .txt files into memory once."""

    if DOCUMENT_CACHE:
        return

    for file in DOCUMENT_DIR.glob("*.txt"):
        DOCUMENT_CACHE[file.name] = file.read_text(
            encoding="utf-8"
        ).strip()


_load_documents()

# ---------- Keyword mapping ----------

KEYWORDS = {
    DIET_GUIDE: [
        "eat",
        "food",
        "diet",
        "meal",
        "nutrition",
        "rice",
        "bread",
        "meat",
        "beef",
        "pork",
        "chicken",
        "fish",
        "vegetable",
        "fruit",
        "egg",
        "salt",
        "sugar",
        "oil",
    ],

    CHOLESTEROL_GUIDE: [
        "cholesterol",
        "ldl",
        "hdl",
        "fat",
        "triglyceride",
    ],

    BP_GUIDE: [
        "blood pressure",
        "bp",
        "hypertension",
    ],

    SMOKING_GUIDE: [
        "smoke",
        "smoking",
        "cigarette",
        "tobacco",
        "vape",
        "alcohol",
        "beer",
        "wine",
        "drink",
    ],

    GENERAL_GUIDE: [
        "exercise",
        "walk",
        "walking",
        "run",
        "running",
        "gym",
        "cardio",
        "heart",
        "risk",
        "healthy",
        "cad",
    ]
}


def get_relevant_knowledge(
    assessment: dict,
    prediction: dict,
    user_message: str,
) -> str:
    """
    Selects the most relevant educational documents
    based on the patient's assessment,
    prediction and latest question.
    """

    selected = set()

    message = user_message.lower()

    # --------------------------------------------------
    # User question
    # --------------------------------------------------

    for filename, keywords in KEYWORDS.items():

        if any(keyword in message for keyword in keywords):
            selected.add(filename)

    # --------------------------------------------------
    # Prediction
    # --------------------------------------------------

    if prediction.get("risk_level") in {"Moderate", "High"}:
        selected.add(GENERAL_GUIDE)

    # --------------------------------------------------
    # Assessment
    # --------------------------------------------------

    if assessment.get("chol", 0) >= 240:
        selected.add(CHOLESTEROL_GUIDE)

    if assessment.get("trestbps", 0) >= 140:
        selected.add(BP_GUIDE)

    if assessment.get("exang", 0) == 1:
        selected.add(GENERAL_GUIDE)

    # Always provide at least one document

    if not selected:
        selected.add(GENERAL_GUIDE)

    return _combine_documents(selected)


def _combine_documents(files: set[str]) -> str:
    """
    Combines multiple documents into one formatted block.
    """

    sections = []

    for filename in sorted(files):

        text = DOCUMENT_CACHE.get(filename)

        if not text:
            continue

        title = filename.removesuffix(".txt")

        sections.append(
            f"""
==================================================
REFERENCE DOCUMENT
{title}
==================================================

{text}
""".strip()
        )

    return "\n\n".join(sections)