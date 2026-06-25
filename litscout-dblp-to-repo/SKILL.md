---
name: litscout-dblp-to-repo
description: "DBLP-driven top-venue paper discovery: curate, enrich abstracts (CrossRef/arXiv/S2/OpenAlex), fetch open-access PDFs, push papers.json+README to a GitHub repo."
---

# LitScout: DBLP → Curated Catalog → GitHub Repo

Turn a research topic into a **curated, top-venue, abstract-enriched paper catalog** (`papers.json` + `README.md`) and push it (plus any open-access PDFs) into a GitHub repo folder.

This is the固化 of the flow Sunnie ran on 2026-06-23 (agent long/short-term memory → 19 top-venue papers → `agent-memory/` folder in `awesome-graph-agent`, with abstracts and 8 PDFs).

## When to use
- "通过 DBLP 找最近顶会顶刊关于 X 的论文，整理到我的仓库 / 建个文件夹"
- Need a reproducible literature catalog with venue, year, DOI, abstract, and (when free) PDF.
- Seeding an idea-discovery / novelty-check pass with a clean corpus.

## Inputs to confirm first
1. **Topic** + a few seed query strings (e.g. "agent long-term memory", "memory poisoning agent").
2. **Venue bar**: top-venue published only, or include landmark CoRR/arXiv preprints? (Default: top-venue published + a few high-signal preprints, year ≥ current−3.)
3. **Target GitHub repo(s)**: catalog repo + folder name; optional separate PDF repo/folder.
4. **Cap**: how many papers after curation (default ~15–25).

## Pipeline

### 1. DBLP search (respect 429)
DBLP is the backbone — authoritative venue/type metadata. Use the public API and **space requests** (it 429s on rapid hits; sleep 2–4s between calls, retry on 429).
```bash
curl -s "https://dblp.org/search/publ/api?q=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))' "agent long-term memory")&format=json&h=30"
```
Run several phrasings. Parse `result.hits.hit[].info` for `title, year, venue, type, key, doi, ee`.

### 2. Curate to top-venue
- **Filter out** `type=="Informal..."` / `venue=="CoRR"` unless it is a landmark/survey you explicitly keep.
- Keep real venues (AAAI/ACL/EMNLP/NeurIPS/ICLR/WWW/SIGIR/EACL/ECIR/TPAMI/CHI/PAKDD…).
- Dedup by DBLP `key`/DOI; keep year ≥ cutoff.
- Cluster by sub-topic for the README (e.g. conversational LTM / architectures / multi-agent & tool memory / security-poisoning / embodied-multimodal).

### 3. Abstract enrichment cascade (DBLP has NO abstracts)
Per paper, try in order until one returns an abstract; record `abstract_src`:
1. **CrossRef** by DOI: `https://api.crossref.org/works/{doi}` → `message.abstract` (JATS XML; strip tags).
2. **arXiv** by title: `http://export.arxiv.org/api/query?search_query=ti:"{title}"&max_results=1`.
3. **Semantic Scholar** by DOI: `https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=abstract` (rate-limited).
4. **OpenAlex** by DOI: `https://api.openalex.org/works/doi:{doi}` → reconstruct from `abstract_inverted_index`.
Expect ~60–100% coverage; recent AAAI/Springer often have none — acceptable, mark `abstract: null`.

### 4. Open-access PDF fetch (best-effort)
Most DOIs (ACM/Springer/IEEE/AAAI) are paywalled → skip. Grab free ones:
- **ACL Anthology** (ACL/EMNLP/EACL/NAACL), **NeurIPS/OpenReview** direct PDF.
- **arXiv fallback**: if an arXiv match exists (step 3), download its PDF.
Record `pdf, pdf_src, pdf_bytes`. Partial coverage (e.g. 8/19) is normal — never fabricate a PDF.

### 5. Emit artifacts
- `papers.json`: objects with `title, year, venue, key, doi, ee, abstract, abstract_src, pdf, pdf_src, pdf_bytes`.
- `README.md`: grouped-by-cluster table (title · venue · year · DOI) + abstracts; note preprint vs published.

### 6. Push to GitHub
- Use the `github` skill. Verify auth + that target repo(s) exist before writing.
- Create the folder, commit `papers.json` + `README.md`; PDFs to the PDF repo/folder if requested.
- Update the repo root README to link the new folder; record commit shas.

## Integrity rules (non-negotiable — Sunnie is a rigorous scholar)
- **Never invent** venues, DOIs, abstract text, or PDF links. If a source doesn't resolve, leave the field null and say so.
- Mark every abstract/author from a secondary source with its `*_src`; flag anything unverified.
- DBLP `type`/`venue` is the source of truth for published-vs-preprint — don't upgrade a CoRR entry without a venue record.
- Keep raw API responses or a fetch log so the catalog is auditable and reruns are cheap.

## Reusable helper (sketch)
Write `build_catalog.py`: load DBLP keys/queries → fetch DBLP → curate → run the 4-source abstract cascade with on-disk caching (sha256 of request) → write `papers.json` + `README.md`. Caching makes reruns free and reproducible.

## Done-check
- `papers.json` parses; every entry has title+venue+year+(doi or key).
- Abstract coverage reported (e.g. "17/20"); nulls explained.
- PDF coverage reported; no fabricated links.
- Repo folder pushed; root README links it; commit shas recorded.