from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.click.crud import create_transaction

router = APIRouter()

from app.click.schema import ClickTransactionCreate
from app.click.utils import generate_url
from app.click.models import ClickTransaction
from app.click.status import (PREPARE, COMPLETE, AUTHORIZATION_FAIL_CODE, AUTHORIZATION_FAIL, ACTION_NOT_FOUND, ORDER_FOUND,
                            ORDER_NOT_FOUND, INVALID_AMOUNT, ALREADY_PAID, TRANSACTION_NOT_FOUND, TRANSACTION_CANCELLED,
                            SUCCESS)



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


@router.post("/transaction/check/")
async def check_order(order_id: str, amount: str):
    if order_id:
        try:
            order = await ClickTransaction.get(id=order_id)
            if int(amount) == order.amount:
                return ORDER_FOUND
            else:
                return INVALID_AMOUNT
        except Exception as e:
            print(e)
            return ORDER_NOT_FOUND


