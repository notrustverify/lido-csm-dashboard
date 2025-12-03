"""API endpoints for the web interface."""

from fastapi import APIRouter, HTTPException

from ..services.operator_service import OperatorService

router = APIRouter()


@router.get("/operator/{identifier}")
async def get_operator(identifier: str):
    """
    Get operator data by address or ID.

    - If identifier is numeric, treat as operator ID
    - If identifier starts with 0x, treat as Ethereum address
    """
    service = OperatorService()

    # Determine if this is an ID or address
    if identifier.isdigit():
        operator_id = int(identifier)
        rewards = await service.get_operator_by_id(operator_id)
    elif identifier.startswith("0x"):
        rewards = await service.get_operator_by_address(identifier)
    else:
        raise HTTPException(status_code=400, detail="Invalid identifier format")

    if rewards is None:
        raise HTTPException(status_code=404, detail="Operator not found")

    return {
        "operator_id": rewards.node_operator_id,
        "manager_address": rewards.manager_address,
        "reward_address": rewards.reward_address,
        "rewards": {
            "current_bond_eth": float(rewards.current_bond_eth),
            "required_bond_eth": float(rewards.required_bond_eth),
            "excess_bond_eth": float(rewards.excess_bond_eth),
            "cumulative_rewards_shares": rewards.cumulative_rewards_shares,
            "distributed_shares": rewards.distributed_shares,
            "unclaimed_shares": rewards.unclaimed_shares,
            "unclaimed_eth": float(rewards.unclaimed_eth),
            "total_claimable_eth": float(rewards.total_claimable_eth),
        },
        "validators": {
            "total": rewards.total_validators,
            "active": rewards.active_validators,
            "exited": rewards.exited_validators,
        },
    }


@router.get("/operators")
async def list_operators():
    """List all operators with rewards in the current tree."""
    service = OperatorService()
    operator_ids = await service.get_all_operators_with_rewards()
    return {"count": len(operator_ids), "operator_ids": operator_ids}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
