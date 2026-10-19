# jobpilot

A Python CLI that automates job-application prep.

## Requirements

- Python 3.11+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python -m jobpilot extract path/to/jd.txt
python -m jobpilot extract path/to/jd.txt --skills my_skills.json
```

`extract` prints the skills found in a job description, one per line. Skills come from
`jobpilot/data/skills.json`, a JSON object of skill → synonyms (the skill name itself
always matches). Matching is case-insensitive and whole-word.

## Test

```bash
python -m pytest
```
