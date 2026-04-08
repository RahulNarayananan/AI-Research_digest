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

    prompt = PROMPT_TEMPLATE.format(
        title    = paper["title"],
        authors  = ", ".join(paper["authors"]),
        abstract = paper["abstract"],
    )

    try:
        genai.configure(api_key=api_key)
        # Using gemini-1.5-flash as it is extremely fast and very generous on the free tier
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        
        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.25,
                top_p=0.90,
                max_output_tokens=600,
            )
        )
        return response.text.strip()

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
    """Return placeholder sections when Ollama is unavailable."""
    abstract_short = paper["abstract"][:350] + "…" if len(paper["abstract"]) > 350 else paper["abstract"]
    return {
        "problem":     abstract_short,
        "solution":    "Read the full paper for the complete methodology.",
        "results":     "Quantitative results are detailed in the paper.",
        "limitations": "Refer to the paper's conclusion for acknowledged limitations.",
        "impact":      (
            f"This paper was ranked as today's highest-impact AI paper based on "
            f"{paper['citation_count']} citations and {paper['influence_score']} influential citations."
        ),
    }
