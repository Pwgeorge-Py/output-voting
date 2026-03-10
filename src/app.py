import itertools
import json
import logging
import random
from datetime import datetime, timezone

import streamlit as st

from input_datamodel import ModelOutputCandidate
from settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [VOTE] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_candidates() -> list[ModelOutputCandidate]:
    """Load and parse candidates from the mounted JSON file."""
    if not settings.candidates_file.exists():
        st.error(
            f"Candidates file not found at `{settings.candidates_file}`. "
            "Mount a JSON file containing a list of ModelOutputCandidate objects."
        )
        st.stop()
    raw = json.loads(settings.candidates_file.read_text())
    return [ModelOutputCandidate(**item) for item in raw]


def build_rounds(
    candidates: list[ModelOutputCandidate],
) -> list[tuple[ModelOutputCandidate, ModelOutputCandidate]]:
    """Group candidates by goal and return all shuffled pairwise combinations."""
    groups: dict[str, list[ModelOutputCandidate]] = {}
    for c in candidates:
        groups.setdefault(c.goal, []).append(c)

    rounds: list[tuple[ModelOutputCandidate, ModelOutputCandidate]] = []
    for group in groups.values():
        pairs = list(itertools.combinations(group, 2))
        random.shuffle(pairs)
        rounds.extend(pairs)

    return rounds


def append_result(result: dict) -> None:
    """Append a single vote result to the shared results file."""
    settings.results_file.parent.mkdir(parents=True, exist_ok=True)
    text = settings.results_file.read_text().strip() if settings.results_file.exists() else ""
    existing = json.loads(text) if text else []
    existing.append(result)
    settings.results_file.write_text(json.dumps(existing, indent=2, default=str))


def record_vote(winner: ModelOutputCandidate, loser: ModelOutputCandidate) -> dict:
    """Build a result dict and log the vote."""
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context_id": winner.context_id,
        "goal": winner.goal,
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
# Session state
# ---------------------------------------------------------------------------

def init_state() -> None:
    """Initialise session state on first load."""
    if "rounds" not in st.session_state:
        candidates = load_candidates()
        rounds = build_rounds(candidates)
        st.session_state.rounds = rounds
        st.session_state.current_idx = 0
        st.session_state.results = []
        st.session_state.done = len(rounds) == 0


def submit_vote(winner: ModelOutputCandidate, loser: ModelOutputCandidate) -> None:
    """Record a vote, persist it, and advance to the next round."""
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
# UI components
# ---------------------------------------------------------------------------

def render_done() -> None:
    """Show the completion screen."""
    st.success(f"All voting rounds complete! {len(st.session_state.results)} votes recorded.")
    st.stop()


def render_progress(idx: int, total: int) -> None:
    """Render the progress bar."""
    st.progress(idx / total, text=f"Round {idx + 1} of {total}")


def render_context(candidate: ModelOutputCandidate) -> None:
    """Render the shared context."""
    with st.expander("Context", expanded=True):
        st.markdown(candidate.context)


def render_voting_columns(
    candidate_a: ModelOutputCandidate, candidate_b: ModelOutputCandidate
) -> None:
    """Render the two side-by-side candidate outputs with vote buttons."""
    st.divider()
    st.caption("Read both outputs below and click **Vote** for the one you prefer.")

    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        st.subheader("Option A")
        st.markdown(candidate_a.output_text)
        if st.button("Vote for Option A", key="vote_a", use_container_width=True, type="primary"):
            submit_vote(candidate_a, candidate_b)
            st.rerun()

    with col_b:
        st.subheader("Option B")
        st.markdown(candidate_b.output_text)
        if st.button("Vote for Option B", key="vote_b", use_container_width=True, type="primary"):
            submit_vote(candidate_b, candidate_a)
            st.rerun()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for the Streamlit app."""
    st.set_page_config(page_title="Output Voting", layout="wide")
    st.title("Model Output Voting")

    init_state()

    if st.session_state.done:
        render_done()

    rounds = st.session_state.rounds
    idx = st.session_state.current_idx
    candidate_a, candidate_b = rounds[idx]

    # Randomise left/right position each round to reduce position bias
    if random.random() < 0.5:
        candidate_a, candidate_b = candidate_b, candidate_a

    render_progress(idx, len(rounds))
    render_context(candidate_a)
    st.header(candidate_a.goal)
    render_voting_columns(candidate_a, candidate_b)


main()
