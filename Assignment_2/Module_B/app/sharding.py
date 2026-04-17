"""Shard routing helpers for sharded ticket operations."""

from app.database import fetch_one
from config import TICKET_SHARD_CONFIGS


def shard_for_member(member_id):
    """Return the canonical shard index for a member."""
    member_id = int(member_id)
    if member_id <= 0:
        raise ValueError("member_id must be positive")
    return (member_id - 1) % 3


def get_ticket_shard_config(shard_idx):
    """Return one shard config by canonical shard index."""
    shard_idx = int(shard_idx)
    if shard_idx not in TICKET_SHARD_CONFIGS:
        raise ValueError(f"Unknown shard index: {shard_idx}")
    return TICKET_SHARD_CONFIGS[shard_idx]


def all_ticket_shards():
    """Return all ticket shard configs in canonical order."""
    return [
        (shard_idx, TICKET_SHARD_CONFIGS[shard_idx])
        for shard_idx in sorted(TICKET_SHARD_CONFIGS)
    ]


def resolve_ticket_shard(ticket_id):
    """Look up the authoritative shard for a ticket from ticket_locator."""
    return fetch_one(
        """
        SELECT ticket_id, member_id, shard_idx, created_at, updated_at
        FROM ticket_locator
        WHERE ticket_id = %s
        """,
        (ticket_id,),
    )
