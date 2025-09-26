from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from app.services.aws.iam import verify_aws_credentials
from app.utils.encryption import encrypt_credentials
from app.utils.jwt_handler import create_access_token

router = APIRouter()


class AWSLoginSchema(BaseModel):
    access_key: str
    secret_key: str


@router.post("/auth/login", tags=["Authentication"])
async def login_for_access_token(form_data: AWSLoginSchema = Body(...)):

    is_valid = await verify_aws_credentials(form_data.access_key, form_data.secret_key)

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid AWS credentials")
    encrypted_creds = encrypt_credentials(form_data.access_key, form_data.secret_key)
    access_token = create_access_token(data={"encrypted_creds": encrypted_creds})

    return {"access_token": access_token, "token_type": "bearer"}