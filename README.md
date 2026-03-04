# output-voting

A Streamlit app for pairwise voting on model output candidates. Annotators are shown two outputs from the same context side-by-side and vote for the preferred one. Results from all users accumulate in a shared JSON file.

## How it works

1. Candidates are loaded from `data/candidates.json` on startup.
2. Candidates with the same `context_id` are grouped together — only candidates from the same group are ever compared.
3. All pairwise combinations within each group are generated and presented in random order.
4. The annotator sees the shared context above two side-by-side outputs and clicks **Vote** for their preferred one.
5. Each vote is logged to stdout and appended to `data/results.json`.
6. Once all pairs are exhausted, the session ends with a completion message.

## Input format

Place a file named `candidates.json` inside the `data/` directory. It must be a JSON array of objects matching the `ModelOutputCandidate` schema:

```json
[
  {
    "uid": "11111111-1111-1111-1111-111111111111",
    "model_name": "gpt-4",
    "context_id": "ctx-001",
    "context": "The shared background text shown to the annotator...",
    "prompt": "The prompt used to generate the output.",
    "output_text": "The model's response to be evaluated.",
    "vote_count": 0,
    "shown_count": 0
  }
]
```

`uid`, `vote_count`, and `shown_count` are optional — they will be auto-populated if omitted.

See [data/sample_candidates.json](data/sample_candidates.json) for a full working example.

## Running with Docker

```bash
# Copy or create your candidates file
cp data/sample_candidates.json data/candidates.json

# Build and start
docker compose up --build
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

Results are written to `data/results.json` on the host after each vote.

## Output format

Each entry in `results.json` represents one pairwise vote:

```json
{
  "timestamp": "2026-03-04T12:00:00+00:00",
  "context_id": "ctx-001",
  "winner_uid": "11111111-1111-1111-1111-111111111111",
  "winner_model": "gpt-4",
  "loser_uid": "22222222-2222-2222-2222-222222222222",
  "loser_model": "claude-3-opus",
  "prompt": "The prompt used to generate the outputs."
}
```

## Project structure

```
output-voting/
├── app.py                      # Streamlit application
├── input_datamodel.py          # ModelOutputCandidate Pydantic model
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── data/
    ├── candidates.json         # Your input file (not committed)
    ├── sample_candidates.json  # Example input
    └── results.json            # Accumulated votes (not committed)
```
