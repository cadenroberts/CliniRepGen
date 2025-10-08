import pdfplumber, json

spans = []
with pdfplumber.open("Prot_SAP_002.pdf") as pdf:
    for page_num, page in enumerate(pdf.pages, start=1):
        text = page.extract_text()
        if text:
            spans.append({
                "doc_id": "Prot_SAP_002",
                "page": page_num,
                "text": text
            })

open("Prot_SAP_002_spans.json", "w").write(json.dumps(spans, indent=2))

