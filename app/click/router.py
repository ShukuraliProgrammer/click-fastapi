from typing import Optional

from fastapi_async_sqlalchemy import db
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1 import crud
from api.v1.crud.base_crud import CRUDBase
from api.v1.helpers.access_to_user import AccessToUser
from api.v1.models import ClickStatusEnum, ClickTransaction, Order, PaymentProvidersEnum, UserPayHistory
from core.babel_config import _
from app.config import settings
from .status import COMPLETE, PREPARE, ACTION_NOT_FOUND, ORDER_NOT_FOUND, \
    INVALID_AMOUNT, ALREADY_PAID, TRANSACTION_NOT_FOUND, TRANSACTION_CANCELLED, SUCCESS, ORDER_FOUND


class PyClickMerchantAPI:
    @classmethod
    async def transaction_load(cls, transaction_id: str, db_session: Optional[AsyncSession] = None):
        db_session = db.session or db_session
        if int(transaction_id) > 1000000000:
            return None
        statement = select(ClickTransaction).where(ClickTransaction.id == int(transaction_id))
        objs = await db_session.execute(statement)
        obj = objs.scalar_one_or_none()
        return obj

    @classmethod
    async def click_webhook_errors(cls, click_trans_id: str,
                                   service_id: str,
                                   merchant_trans_id: str,
                                   amount: str,
                                   action: str,
                                   sign_time: str,
                                   sign_string: str,
                                   error: str,
                                   merchant_prepare_id: str = None) -> dict:
        if action not in [PREPARE, COMPLETE]:
            return {
                'error': ACTION_NOT_FOUND,
                'error_note': _('Action not found')
            }

        transaction = await cls.transaction_load(merchant_trans_id)
        if not transaction:
            return {
                'error': ORDER_NOT_FOUND,
                'error_note': _('Order not found')
            }

        if abs(float(amount) - float(transaction.amount) > 0.01):
            return {
                'error': INVALID_AMOUNT,
                'error_note': _('Incorrect parameter amount')
            }

        if transaction.status == ClickStatusEnum.CONFIRMED.value:
            return {
                'error': ALREADY_PAID,
                'error_note': _('Already paid')
            }

        if action == COMPLETE:
            if merchant_trans_id != merchant_prepare_id:
                return {
                    'error': TRANSACTION_NOT_FOUND,
                    'error_note': _('Transaction not found')
                }
        if transaction.status == ClickStatusEnum.CANCELED.value or int(error) < 0:
            return {
                'error': TRANSACTION_CANCELLED,
                'error_note': _('Transaction cancelled')
            }
        return {
            'error': SUCCESS,
            'error_note': 'Success'
        }

    @classmethod
    async def prepare(cls, click_trans_id: str,
                      service_id: str,
                      click_paydoc_id: str,
                      merchant_trans_id: str,
                      amount: str,
                      action: str,
                      sign_time: str,
                      sign_string: str,
                      error: str,
                      error_note: str,
                      db_session: Optional[AsyncSession] = None,
                      *args, **kwargs) -> dict:
        """
        :param click_trans_id:
        :param service_id:
        :param click_paydoc_id:
        :param merchant_trans_id:
        :param amount:
        :param action:
        :param sign_time:
        :param sign_string:
        :param error:
        :param error_note:
        :param db_session:
        :param args:
        :param kwargs:
        :return:
        """
        db_session = db.session or db_session
        transaction = await cls.transaction_load(merchant_trans_id)
        result = {
            "error": SUCCESS,
        }
        transaction.status = ClickStatusEnum.WAITING
        db_session.add(transaction)
        await db_session.commit()

        result['click_trans_id'] = click_trans_id
        result['merchant_trans_id'] = merchant_trans_id
        result['merchant_prepare_id'] = merchant_trans_id
        result['merchant_confirm_id'] = merchant_trans_id
        return result

    @classmethod
    async def complete(cls, click_trans_id: str,
                       service_id: str,
                       click_paydoc_id: str,
                       merchant_trans_id: str,
                       amount: str,
                       action: str,
                       sign_time: str,
                       sign_string: str,
                       error: str,
                       error_note: str,
                       merchant_prepare_id: str = None,
                       db_session: Optional[AsyncSession] = None,
                       *args, **kwargs) -> dict:
        """
        :param click_trans_id:
        :param service_id:
        :param click_paydoc_id:
        :param merchant_trans_id:
        :param amount:
        :param action:
        :param sign_time:
        :param sign_string:
        :param error:
        :param error_note:
        :param merchant_prepare_id:
        :param db_session:
        :param args:
        :param kwargs:
        :return:
        """
        db_session = db.session or db_session
        transaction = await cls.transaction_load(merchant_trans_id)
        result = await cls.click_webhook_errors(click_trans_id, service_id, merchant_trans_id,
                                                amount, action, sign_time, sign_string, error, merchant_prepare_id)
        if error and int(error) < 0:
            transaction.status = ClickStatusEnum.CANCELED
        if result['error'] == SUCCESS:
            transaction.status = ClickStatusEnum.CONFIRMED
            transaction.click_paydoc_id = click_paydoc_id
        db_session.add(transaction)
        await db_session.commit()
        await cls.successfully_payment(transaction=transaction, db_session=db_session)
        result['click_trans_id'] = click_trans_id
        result['merchant_trans_id'] = merchant_trans_id
        result['merchant_prepare_id'] = merchant_prepare_id
        result['merchant_confirm_id'] = merchant_prepare_id
        return result

    @staticmethod
    async def generate_url(order_id, amount, return_url=None):
        service_id = settings.CLICK_SETTINGS['service_id']
        merchant_id = settings.CLICK_SETTINGS['merchant_id']
        url = f"https://my.click.uz/services/pay?service_id={service_id}&merchant_id={merchant_id}&amount={amount}&transaction_param={order_id}"
        if return_url:
            url += f"&return_url={return_url}"
        return url

    @classmethod
    async def successfully_payment(cls, transaction: ClickTransaction, db_session: Optional[AsyncSession] = None):
        """ Эта функция вызывается после успешной оплаты """
        db_session = db.session or db_session
        print(f"Successfully payment from CLICK\nTransaction ID: {transaction.id}")
        order = await crud.order.get(
            where={Order.payment_provider: PaymentProvidersEnum.CLICK, Order.transaction_id: transaction.id})
        _crud = CRUDBase(UserPayHistory)
        pay_history = await _crud.get(where={UserPayHistory.id: order.user_pay_history_id}, db_session=db_session)

        pay_history.is_paid = True
        order.is_paid = True
        db_session.add_all([order, pay_history])
        await db_session.commit()

        await AccessToUser.open_access(pay_history.user_purchase_id, db_session=db_session)

    @classmethod
    async def check_order(cls, order_id: str, amount: str):
        try:
            if order_id:
                transaction = await cls.transaction_load(order_id)
                if transaction:
                    if float(amount) == transaction.amount:
                        return ORDER_FOUND
                    else:
                        return INVALID_AMOUNT
                else:
                    return ORDER_NOT_FOUND
        except SQLAlchemyError:
            return ORDER_NOT_FOUND

    @classmethod
    async def create_transaction(cls, amount: float, order: Order) -> str:
        return_url = 'http://topskill.uz/profile'
        db_session = db.session

        transaction = ClickTransaction(amount=amount)
        db_session.add(transaction)
        await db_session.commit()

        order.transaction_id = transaction.id
        db_session.add(order)
        await db_session.commit()

        url = await PyClickMerchantAPI.generate_url(order_id=transaction.id, amount=str(amount), return_url=return_url)
        return url