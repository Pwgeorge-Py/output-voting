# output-voting

A Streamlit app for pairwise voting on model output candidates. Annotators are shown two outputs from the same context side-by-side and vote for the preferred one. After voting, annotators are shown a single "best" output and asked to provide improvement suggestions. Results from all users accumulate in a shared JSON file.

## How it works

1. Candidates are loaded from `data/candidates.json` on startup.
2. Candidates with the same `goal` are grouped together — only candidates from the same group are ever compared.
3. All pairwise combinations within each group are generated and presented in random order.
4. The annotator sees the shared context above two side-by-side outputs and clicks **Vote** for their preferred one.
5. Each vote is logged to stdout and appended to `data/results.json`.
6. Once all pairs are exhausted, a feedback stage begins: the annotator is shown the output from `data/feedback_file.json` and asked for improvement suggestions.
7. Feedback is appended to `data/results.json` and the session ends with a completion message.

## Input format

### candidates.json

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
    "goal": "model comparison",
    "vote_count": 0,
    "shown_count": 0
  }
]
```

`uid`, `goal`, `vote_count`, and `shown_count` are optional — they will be auto-populated if omitted. The `goal` field (default: `"unspecified"`) is used to group candidates: only candidates sharing the same `goal` are compared against each other.

See [data/sample_candidates.json](data/sample_candidates.json) for a full working example.

### feedback_file.json

A single `ModelOutputCandidate` object (not an array) placed at `data/feedback_file.json`. This output is shown to annotators after voting completes to collect improvement suggestions.

```json
{
  "uid": "11111111-1111-1111-1111-111111111111",
  "model_name": "gpt-4",
  "context_id": "ctx-001",
  "context": "The shared background text...",
  "prompt": "The prompt used to generate the output.",
  "output_text": "The model's response to be evaluated.",
  "goal": "model comparison"
}
```

See [sample_feedback_file.json](sample_feedback_file.json) for a full working example.

## Configuration

Copy `.env.template` to `.env` and adjust as needed:

```bash
cp .env.template .env
```

| Variable | Default | Description |
|---|---|---|
| `DATA_DIR` | `/data` | Directory containing `candidates.json` and where `results.json` is written |

## Running with Docker

```bash
# Copy or create your input files
cp data/sample_candidates.json data/candidates.json

# Build and start
docker compose up --build
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

Results are written to `data/results.json` on the host after each vote.

## Output format

`results.json` contains a JSON array. Each entry is either a **vote** or **feedback** record.

### Vote entry

```json
{
  "timestamp": "2026-03-04T12:00:00+00:00",
  "context_id": "ctx-001",
  "goal": "model comparison",
  "winner_uid": "11111111-1111-1111-1111-111111111111",
  "winner_model": "gpt-4",
  "loser_uid": "22222222-2222-2222-2222-222222222222",
  "loser_model": "claude-3-opus",
  "prompt": "The prompt used to generate the outputs."
}
```

### Feedback entry

```json
{
  "timestamp": "2026-03-04T12:05:00+00:00",
  "type": "improvement_feedback",
  "context_id": "ctx-001",
  "goal": "model comparison",
  "candidate_uid": "11111111-1111-1111-1111-111111111111",
  "candidate_model": "gpt-4",
  "feedback": "Needs to follow a specific format..."
}
```

## Project structure

```
output-voting/
├── src/
│   ├── app.py                      # Streamlit application
│   ├── input_datamodel.py          # ModelOutputCandidate Pydantic model
│   └── settings.py                 # Pydantic settings (reads .env)
├── .env.template                   # Example environment configuration
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── sample_feedback_file.json       # Example feedback candidate
└── data/
    ├── candidates.json             # Your input file (not committed)
    ├── feedback_file.json          # Feedback stage candidate (not committed)
    ├── sample_candidates.json      # Example candidates input
    └── results.json                # Accumulated votes and feedback (not committed)
```
