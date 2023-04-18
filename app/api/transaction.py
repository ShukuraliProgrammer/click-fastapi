from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.click.crud import create_transaction
from .pyclick_merchant import click_merchant

router = APIRouter()

from app.click.schema import ClickTransactionCreate
from app.click.utils import generate_url



@router.post("/transaction/create/")
async def create_click_transaction(
        transaction_in: ClickTransactionCreate,
):
    inform = await create_transaction(transaction_in.click_paydoc_id, transaction_in.amount, transaction_in.action,
                                      transaction_in.status)

    return_url = 'http://127.0.0.1:8000/'
    url = generate_url(order_id=inform.id, amount=str(transaction_in.amount), return_url=return_url)
    return {
        "link": url,
    }


