"""
summarizer.py — Generates a structured research summary using Ollama (local LLM).

The summary is structured into five sections:
    PROBLEM      — gap / challenge the paper addresses
    SOLUTION     — core methodology / architecture / approach
    RESULTS      — key quantitative outcomes / benchmarks
    LIMITATIONS  — acknowledged shortcomings or future work
    IMPACT       — why this matters for the AI community

Ollama must be running locally:  ollama serve
Model must be pulled first:      ollama pull mistral
"""

import os
import google.generativeai as genai

PROMPT_TEMPLATE = """\
You are an expert AI researcher writing for a technical-but-accessible daily digest.

Analyze the paper below and write a structured summary with EXACTLY these six sections.
Each section should be strictly 1-2 brief, high-impact sentences. Be specific — mention method names,
numbers, benchmarks where available. Do not use markdown headers, just the bold text.

Title:    {title}
Authors:  {authors}
Abstract: {abstract}

Respond using ONLY this exact format (keep the bold markers at the start of the line):

**PROBLEM:**
<your text>

**SOLUTION:**
<your text>

**RESULTS:**
<your text>

**LIMITATIONS:**
<your text>

**IMPACT:**
<your text>

**WHY IT MATTERS:**
<Give a brief reasoning on why this paper is currently a hot topic and assign a 'Relevance Score' out of 10 based on industry buzz.>
"""


def summarize_paper(paper: dict, model: str = "") -> str | None:
    """Call Google Gemini API and return the raw summary string, or None on failure."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[ERROR] GEMINI_API_KEY is not set in .env")
        return None

    abstract = paper.get("abstract", "").strip()
    if not abstract:
        print(f"[WARN] No abstract available for: {paper.get('title', 'Unknown')}")
        return None

    authors = paper.get("authors") or ["Unknown"]

    prompt = PROMPT_TEMPLATE.format(
        title    = paper.get("title", ""),
        authors  = ", ".join(authors),
        abstract = abstract,
    )

    try:
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        
        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                top_p=0.90,
                max_output_tokens=1024,  # Increased: 6 sections need more room
            )
        )
        raw = response.text.strip()
        print(f"      [GEMINI] Raw response ({len(raw)} chars): {raw[:120]}...")
        return raw

    except Exception as exc:
        print(f"[ERROR] Gemini API Summarization failed: {exc}")

    return None


import re

def parse_summary(text: str) -> dict[str, str]:
    """
    Parse the LLM output into a dict with keys:
        problem, solution, results, limitations, impact, why_it_matters
    """
    sections = {k: "" for k in ("problem", "solution", "results", "limitations", "impact", "why_it_matters")}

    if not text:
        return sections

    # Robust regex to catch sections
    header_pattern = re.compile(
        r'^\s*(?:\d+\.)?\s*#*\s*\*?\*?\s*(PROBLEM|SOLUTION|RESULTS|LIMITATIONS|IMPACT|WHY IT MATTERS)\s*\*?\*?\s*:?', 
        re.IGNORECASE
    )

    current_section = None
    
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
            
        match = header_pattern.search(stripped)
        if match and match.start() == 0:
            current_section = match.group(1).lower().replace(" ", "_")
            
            # Check if there is actual text on the same line
            after_header = stripped[match.end():].strip().strip("*").strip()
            if after_header:
                sections[current_section] = after_header
        elif current_section:
            # Append subsequent lines to the current section
            sep = " " if sections[current_section] else ""
            sections[current_section] += sep + stripped

    # Clean up formatting
    for k in sections:
        sections[k] = sections[k].replace("**", "").strip()

    return sections


def fallback_sections(paper: dict) -> dict[str, str]:
    """Return best-effort sections from abstract when Gemini is unavailable."""
    abstract = paper.get("abstract", "") or ""
    # Split abstract into rough halves to approximate problem/solution
    mid = len(abstract) // 2
    problem_text  = abstract[:mid].strip() or "See abstract for details."
    solution_text = abstract[mid:].strip() or "See abstract for details."

    return {
        "problem":         problem_text,
        "solution":        solution_text,
        "results":         "See the paper for quantitative results.",
        "limitations":     "See the paper's conclusion for limitations.",
        "impact":          "This paper was selected based on trending signals from Hugging Face and Papers With Code.",
        "why_it_matters":  "This paper is currently trending in the AI research community.",
    }
