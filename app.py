import itertools
import json
import logging
import os
import random
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from input_datamodel import ModelOutputCandidate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [VOTE] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
CANDIDATES_FILE = DATA_DIR / "candidates.json"
RESULTS_FILE = DATA_DIR / "results.json"


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_candidates() -> list[ModelOutputCandidate]:
    if not CANDIDATES_FILE.exists():
        st.error(f"Candidates file not found at `{CANDIDATES_FILE}`. "
                 "Mount a JSON file containing a list of ModelOutputCandidate objects.")
        st.stop()
    raw = json.loads(CANDIDATES_FILE.read_text())
    return [ModelOutputCandidate(**item) for item in raw]


def build_rounds(candidates: list[ModelOutputCandidate]) -> list[tuple[ModelOutputCandidate, ModelOutputCandidate]]:
    """Group by context_id and generate all pairwise combinations within each group."""
    groups: dict[str, list[ModelOutputCandidate]] = {}
    for c in candidates:
        groups.setdefault(c.context_id, []).append(c)

    rounds: list[tuple[ModelOutputCandidate, ModelOutputCandidate]] = []
    for group in groups.values():
        pairs = list(itertools.combinations(group, 2))
        random.shuffle(pairs)
        rounds.extend(pairs)

    return rounds


def append_result(result: dict) -> None:
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(RESULTS_FILE.read_text()) if RESULTS_FILE.exists() else []
    existing.append(result)
    RESULTS_FILE.write_text(json.dumps(existing, indent=2, default=str))


def record_vote(winner: ModelOutputCandidate, loser: ModelOutputCandidate) -> dict:
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context_id": winner.context_id,
        "winner_uid": str(winner.uid),
        "winner_model": winner.model_name,
        "loser_uid": str(loser.uid),
        "loser_model": loser.model_name,
        "prompt": winner.prompt,
    }
    logger.info(
        "vote | context_id=%s | winner=%s (%s) | loser=%s (%s)",
        result["context_id"],
        result["winner_uid"],
        result["winner_model"],
        result["loser_uid"],
        result["loser_model"],
    )
    return result


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def init_state():
    if "rounds" not in st.session_state:
        candidates = load_candidates()
        rounds = build_rounds(candidates)
        st.session_state.rounds = rounds
        st.session_state.current_idx = 0
        st.session_state.results = []
        st.session_state.done = len(rounds) == 0


def vote(winner: ModelOutputCandidate, loser: ModelOutputCandidate):
    result = record_vote(winner, loser)
    winner.vote_count += 1
    winner.shown_count += 1
    loser.shown_count += 1
    st.session_state.results.append(result)
    append_result(result)
    st.session_state.current_idx += 1
    if st.session_state.current_idx >= len(st.session_state.rounds):
        st.session_state.done = True


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Output Voting", layout="wide")
st.title("Model Output Voting")

init_state()

if st.session_state.done:
    st.success(f"All voting rounds complete! {len(st.session_state.results)} votes recorded.")
    st.stop()

rounds = st.session_state.rounds
idx = st.session_state.current_idx
total = len(rounds)
candidate_a, candidate_b = rounds[idx]

# Randomise left/right position each round to reduce position bias
if random.random() < 0.5:
    candidate_a, candidate_b = candidate_b, candidate_a

# Progress
st.progress((idx) / total, text=f"Round {idx + 1} of {total}  ·  context: `{candidate_a.context_id}`")

# Context
with st.expander("Context", expanded=True):
    st.markdown(candidate_a.context)

st.divider()
st.caption("Read both outputs below and click **Vote** for the one you prefer.")

col_a, col_b = st.columns(2, gap="large")

with col_a:
    st.subheader("Option A")
    st.markdown(candidate_a.output_text)
    if st.button("Vote for Option A", key="vote_a", use_container_width=True, type="primary"):
        vote(candidate_a, candidate_b)
        st.rerun()

with col_b:
    st.subheader("Option B")
    st.markdown(candidate_b.output_text)
    if st.button("Vote for Option B", key="vote_b", use_container_width=True, type="primary"):
        vote(candidate_b, candidate_a)
        st.rerun()
