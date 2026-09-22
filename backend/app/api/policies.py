from fastapi import APIRouter
from app.services.policy_service import list_policies

router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.get("")
def policies():
    return list_policies()
