import time
import hashlib
import json
from typing import Union, Optional
import requests
from fastapi_async_sqlalchemy import db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.click.models import ClickTransaction
from app.click.status import ClickStatusEnum, SUCCESS, ALREADY_PAID

from app.config import settings


class ApiHelper:
    endpoint = 'https://api.click.uz/v2/merchant'

    def __init__(self, data):
        self.data = data
        self.transaction_id = data.get('transaction_id', None)
        self.timestamps = int(time.time())
        self.merchant_user_id = settings.CLICK_SETTINGS['merchant_user_id']
        self.service_id = settings.CLICK_SETTINGS['service_id']
        self.token = hashlib.sha1('{timestamps}{secret_key}'.format(
            timestamps=self.timestamps, secret_key=settings.CLICK_SETTINGS['secret_key']
        ).encode('utf-8')).hexdigest()

    @classmethod
    def get_extra_data(cls, transaction: ClickTransaction):
        extra_data = {}
        try:
            extra_data = json.loads(transaction.extra_data)
        except Exception:
            pass
        return extra_data

    @classmethod
    async def save_extra_data(cls, transaction: ClickTransaction, extra_data: dict,
                              db_session: Optional[AsyncSession] = None):
        db_session = db.session or db_session
        transaction.extra_data = json.dumps(extra_data)
        db_session.add(transaction)
        await db_session.commit()

    def post(self, url: str, data: dict):
        response = requests.post(self.endpoint + url, json=data, headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Auth': '{}:{}:{}'.format(self.merchant_user_id, self.token, self.timestamps)
        })
        return response

    def get(self, url: str):
        response = requests.get(self.endpoint + url, headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Auth': '{}:{}:{}'.format(self.merchant_user_id, self.token, self.timestamps)
        })
        return response

    def delete(self, url: str):
        response = requests.delete(self.endpoint + url, headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Auth': '{}:{}:{}'.format(self.merchant_user_id, self.token, self.timestamps)
        })
        return response

    @classmethod
    def make_error_response(cls, status_code: int) -> dict:
        return {
            'status': -1 * status_code,
            'status_note': 'Http request error [{}]'.format(status_code)
        }

    @classmethod
    def get_transaction(cls, transaction_id: int, db_session: Optional[AsyncSession] = None) -> \
            Union[Optional[ClickTransaction], dict]:
        db_session = db.session or db_session

        statement = select(ClickTransaction).where(ClickTransaction.id == int(transaction_id))
        objs = await db_session.execute(statement)
        obj = objs.scalar_one_or_none()
        if obj:
            return obj
        else:
            return {
                'error': -5001,
                'error_note': 'Transaction not found'
            }

    async def create_invoice(self):
        transaction = await self.get_transaction(self.transaction_id)
        if isinstance(transaction, ClickTransaction):
            invoice = self.post('/invoice/create', {
                'service_id': self.service_id,
                'amount': float(transaction.amount),
                'phone_number': self.data['phone_number'],
                'merchant_trans_id': self.transaction_id
            })
            if invoice.status_code == 200:
                _json = invoice.json()
                extra_data = self.get_extra_data(transaction)
                extra_data['payment'] = {
                    'type': 'phone_number',
                    'phone_number': self.data['phone_number'],
                    'invoice': _json
                }
                await self.save_extra_data(transaction, extra_data)
                if _json['error_code'] == SUCCESS:
                    transaction.change_status(ClickStatusEnum.PROCESSING.value)
                else:
                    transaction.change_status(ClickStatusEnum.ERROR.value)
                transaction.message = json.dumps(_json)
                await self.save_transaction(transaction)
                return _json
            return self.make_error_response(invoice.status_code)
        else:
            return transaction

    async def check_invoice(self):
        transaction = await self.get_transaction(self.transaction_id)
        if isinstance(transaction, ClickTransaction):
            check_invoice = self.get('/invoice/status/{service_id}/{invoice_id}'.format(
                service_id=self.service_id,
                invoice_id=self.data['invoice_id']
            ))
            if check_invoice.status_code == 200:
                _json = check_invoice.json()
                if _json['status'] > 0:
                    transaction.change_status(ClickStatusEnum.CONFIRMED.value)
                elif _json['status'] == -99:
                    transaction.change_status(ClickStatusEnum.CANCELED.value)
                elif _json['status'] < 0:
                    transaction.change_status(ClickStatusEnum.ERROR.value)
                transaction.message = json.dumps(_json)
                await self.save_transaction(transaction)
                return _json
            return self.make_error_response(check_invoice.status_code)
        else:
            return transaction

    async def check_payment_status(self):
        transaction = await self.get_transaction(self.transaction_id)
        if isinstance(transaction, ClickTransaction):
            check_payment = self.get('/payment/status/{service_id}/{payment_id}'.format(
                service_id=self.service_id,
                payment_id=transaction.click_paydoc_id
            ))
            if check_payment.status_code == 200:
                _json = check_payment.json()
                if _json['payment_status'] and _json['payment_status'] == 2:
                    transaction.change_status(ClickStatusEnum.CONFIRMED.value)
                elif _json['payment_status'] and _json['payment_status'] < 0:
                    transaction.change_status(ClickStatusEnum.ERROR.value)
                transaction.message = json.dumps(_json)
                await self.save_transaction(transaction)
                return _json
            return self.make_error_response(check_payment.status_code)
        else:
            return transaction

    async def create_card_token(self):
        transaction = await self.get_transaction(self.transaction_id)
        if isinstance(transaction, ClickTransaction):
            if transaction.status == ClickStatusEnum.CONFIRMED.value:
                return {
                    'error': ALREADY_PAID,
                    'error_note': 'Transaction already paid'
                }
            data = {
                'service_id': self.service_id,
                'card_number': self.data['card_number'],
                'expire_date': self.data['expire_date'],
                'temporary': self.data['temporary']
            }
            response = self.post('/card_token/request', data=data)
            if response.status_code == 200:
                _json = response.json()
                extra_data = self.get_extra_data(transaction)
                extra_data['payment'] = {
                    'type': 'card_number',
                    'card_number': self.data['card_number'],
                    'temporary': self.data['temporary'],
                    'card_token': _json
                }
                await self.save_extra_data(transaction, extra_data)
                if _json['error_code'] == 0:
                    transaction.change_status(ClickStatusEnum.PROCESSING.value)
                else:
                    transaction.change_status(ClickStatusEnum.ERROR.value)
                transaction.message = json.dumps(_json)
                await self.save_transaction(transaction)
                return _json
            return self.make_error_response(response.status_code)
        else:
            return transaction

    async def verify_card_token(self):
        transaction = await self.get_transaction(self.transaction_id)
        if isinstance(transaction, ClickTransaction):
            if transaction.status != ClickStatusEnum.PROCESSING.value:
                return {
                    'error': -5001,
                    'error_note': 'Transaction is not ready'
                }
            data = {
                'service_id': self.service_id,
                'card_token': self.data['card_token'],
                'sms_code': self.data['sms_code']
            }
            response = self.post('/card_token/verify', data)
            if response.status_code == 200:
                _json = response.json()
                if not _json['error_code'] == 0:
                    transaction.change_status(ClickStatusEnum.ERROR.value)
                transaction.message = json.dumps(_json)
                await self.save_transaction(transaction)
                return _json
            return self.make_error_response(response.status_code)
        else:
            return transaction

    async def payment_with_token(self):
        transaction = await self.get_transaction(self.transaction_id)
        if isinstance(transaction, ClickTransaction):
            if transaction.status != ClickStatusEnum.PROCESSING.value:
                return {
                    'error': -5001,
                    'error_note': 'Transaction is not ready'
                }
            data = {
                "service_id": self.service_id,
                "card_token": self.data['card_token'],
                "amount": str(transaction.amount),
                "transaction_parameter": self.transaction_id
            }
            response = self.post('/card_token/payment', data=data)
            if response.status_code == 200:
                _json = response.json()
                if _json['error_code'] == 0:
                    transaction.change_status(ClickStatusEnum.CONFIRMED.value)
                else:
                    transaction.change_status(ClickStatusEnum.ERROR.value)
                transaction.click_paydoc_id = _json['payment_id']
                transaction.message = json.dumps(_json)
                await self.save_transaction(transaction)
                return _json
            return self.make_error_response(response.status_code)
        else:
            return transaction

    async def delete_card_token(self):
        data = {
            'service_id': self.service_id,
            'card_token': self.data['card_token']
        }
        response = self.delete('/card_token/{service_id}/{card_token}'.format(**data))
        if response.status_code == 200:
            return response.json()
        return self.make_error_response(response.status_code)

    async def cancel_payment(self):
        transaction = self.get_transaction(self.transaction_id)
        if isinstance(transaction, ClickTransaction):
            data = {
                'service_id': self.service_id,
                'payment_id': transaction.click_paydoc_id
            }
            response = self.delete('/payment/reversal/{service_id}/{payment_id}'.format(**data))
            if response.status_code == 200:
                _json = response.json()
                if _json['error_code'] == 0:
                    transaction.change_status(ClickStatusEnum.CANCELED.value)
                transaction.message = json.dumps(_json)
                await self.save_transaction(transaction)
                return _json
            return self.make_error_response(response.status_code)
        return transaction

    @classmethod
    async def save_transaction(cls, transaction: ClickTransaction, db_session: Optional[AsyncSession] = None):
        db_session = db.session or db_session
        db_session.add(transaction)
        await db_session.commit()


class Services(ApiHelper):
    def __init__(self, data, service_type):
        self.data = data
        self.service_type = service_type
        super().__init__(self.data)

    def api(self):
        if self.service_type == 'create_invoice':
            return self.create_invoice()
        elif self.service_type == 'check_invoice':
            return self.check_invoice()
        elif self.service_type == 'check_payment_status':
            return self.check_payment_status()
        elif self.service_type == 'create_card_token':
            return self.create_card_token()
        elif self.service_type == 'verify_card_token':
            return self.verify_card_token()
        elif self.service_type == 'payment_with_token':
            return self.payment_with_token()
        elif self.service_type == 'delete_card_token':
            return self.delete_card_token()
        elif self.service_type == 'cancel_payment':
            return self.cancel_payment()
        else:
            return {
                'error': -1000,
                'error_note': 'Service type could not be detected'
            }