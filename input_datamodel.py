from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ModelOutputCandidate(BaseModel):
    uid: UUID = Field(default_factory=uuid4)
    model_name: str
    context_id: str # ID of external knowledge used to build the prompt
    context: str # external knowledge that was used to build the prompt
    prompt: str # prompt used to generate output_text
    output_text: str
    vote_count: int = 0 # Number of times canidate was voted for out of options
    shown_count: int = 0 # Number of times candidate shown to user
