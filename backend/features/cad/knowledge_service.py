from pathlib import Path

DOCUMENT_DIR = Path(__file__).resolve().parent / "documents"

GENERAL_GUIDE = "How To Keep Your Heart Healthy The Essential Dos and Donts.txt"
DIET_GUIDE = "Heart Health Basic Dietary Guidelines.txt"
CHOLESTEROL_GUIDE = "Cholesterol and Heart Disease.txt"
BP_GUIDE = "High Blood Pressure Healthy Eating Guide.txt"
SMOKING_GUIDE = "Alcohol and Smoking.txt"

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

KEYWORDS = {
    DIET_GUIDE: [
        "eat", "food", "diet", "meal", "nutrition", "rice", "bread", "meat", "beef",
        "pork", "chicken", "fish", "vegetable", "fruit", "salt", "sodium", "fat",
        "oil", "sugar", "sweet", "carb", "carbohydrate", "protein", "cholesterol"
    ],
    CHOLESTEROL_GUIDE: [
        "cholesterol", "ldl", "hdl", "triglyceride", "plaque", "artery", "arteries",
        "fat", "saturate", "trans fat", "egg", "seafood", "prawn", "squid", "organ",
        "liver", "dairy", "milk", "cheese", "butter"
    ],
    BP_GUIDE: [
        "pressure", "blood pressure", "hypertension", "bp", "salt", "sodium",
        "sauce", "canned", "process", "gravy", "soup", "monosodium", "msg"
    ],
    SMOKING_GUIDE: [
        "smoke", "smoking", "cigarette", "tobacco", "nicotine", "vape", "vaping",
        "alcohol", "beer", "wine", "liquor", "spirit", "drink", "drinking"
    ]
}


def get_relevant_knowledge(
    assessment: dict,
    prediction: dict,
    user_message: str
) -> str:
    message_lower = user_message.lower()
    matched_docs = set()

    for doc_name, keywords in KEYWORDS.items():
        for keyword in keywords:
            if keyword in message_lower:
                matched_docs.add(doc_name)
                break

    if not matched_docs:
        matched_docs.add(GENERAL_GUIDE)

    sections = []
    for doc in matched_docs:
        content = DOCUMENT_CACHE.get(doc)
        if content:
            sections.append(f"--- DOCUMENT: {doc} ---\n{content}")

    return "\n\n".join(sections)
