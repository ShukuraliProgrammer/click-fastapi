from app.click.schema import ClickTransactionCreate
from app.click.status import (PREPARE, COMPLETE, AUTHORIZATION_FAIL_CODE, AUTHORIZATION_FAIL, ACTION_NOT_FOUND,
                              ORDER_FOUND)
from app.click.utils import authorization, prepare, complete

from fastapi import APIRouter, Depends, HTTPException, Request

router = APIRouter()
from app.click.models import ClickTransaction
from app.click.status import (PREPARE, COMPLETE, AUTHORIZATION_FAIL_CODE, AUTHORIZATION_FAIL, ACTION_NOT_FOUND,
                              ORDER_FOUND,
                              ORDER_NOT_FOUND, INVALID_AMOUNT, ALREADY_PAID, TRANSACTION_NOT_FOUND,
                              TRANSACTION_CANCELLED,
                              SUCCESS)



async def check_order(order_id: str, amount: str):
    print("order_id", order_id)
    if order_id:
        try:
            print("order_id", order_id)
            order = await ClickTransaction.get(id=order_id)
            print("order", order.amount)
            if int(amount) == order.amount:
                print("order.amount", order.amount)
                return ORDER_FOUND
            else:
                return INVALID_AMOUNT
        except Exception as e:
            print(e)
            return ORDER_NOT_FOUND

@router.post("/transaction/")
async def click_merchant(trans_info: ClickTransactionCreate):
    click_merchant_in = trans_info.dict(exclude_unset=True)
    print(click_merchant_in)
    METHODS = {
        PREPARE: prepare,
        COMPLETE: complete
    }

    merchant_trans_id = click_merchant_in.get('merchant_trans_id')
    amount = click_merchant_in.get('amount')
    action = click_merchant_in.get('action')
    if authorization(click_trans_id=click_merchant_in.get('click_trans_id'),
                     service_id=click_merchant_in.get('service_id'),
                     amount=click_merchant_in.get('amount'),
                     action=click_merchant_in.get('action'),
                     sign_time=click_merchant_in.get('sign_time'),
                     sign_string=click_merchant_in.get('sign_string'),
                     error=click_merchant_in.get('error'),
                     merchant_trans_id=click_merchant_in.get('merchant_trans_id'),
                     merchant_prepare_id=click_merchant_in.get('merchant_prepare_id')) is False:
        return {
            "error": AUTHORIZATION_FAIL_CODE,
            "error_note": AUTHORIZATION_FAIL
        }

    # assert self.VALIDATE_CLASS
    ch_order = await check_order(order_id=merchant_trans_id, amount=amount)
    print("ch_order", ch_order)
    if ch_order is True:
        print("action", action)
        result = METHODS[action](**click_merchant_in)
        return result
    return {"error": check_order}
