from fastapi import APIRouter, Body
from controllers.role_controller import AIRoleController

router = APIRouter()
role_controller = AIRoleController()

@router.post("/role/prompt")
def get_role_prompt(payload: dict = Body(...)):
    """
    Returns the formatted role prompt.
    Expects a JSON body with keys matching the placeholders.
    """
    return {"prompt": role_controller.get_role_prompt(**payload)}

@router.get("/role/placeholders")
def get_placeholders():
    """
    Returns the list of placeholders in the role prompt.
    """
    return {"placeholders": role_controller.get_placeholders()}
