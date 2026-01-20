from fastapi import FastAPI, HTTPException

from transformers import pipeline

from models import AnalyzeRequest, AnalyzeResponse

app = FastAPI()


# zs_clf = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1")
zs_clf = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    try:
        text = req.text.strip()

        # 1) Multi-label zero-shot for the three categories
        labels = [
            "violent acts",
            "sexual content",
            "illegal activity",
        ]
        zs = zs_clf(text, candidate_labels=labels, multi_label=True)
        print(zs)
        scores = {lbl: float(score) for lbl, score in zip(zs["labels"], zs["scores"])}

        violence = scores.get("violent acts", 0.0)
        sexual = scores.get("sexual content", 0.0)
        illegal = scores.get("illegal activity", 0.0)

        # 2) Overall toxicity can be "max risk"
        toxicity = max(violence, sexual, illegal)

        return AnalyzeResponse(
            toxicity=toxicity,
            sexual=sexual,
            violence=violence,
            illegal=illegal
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {e}")