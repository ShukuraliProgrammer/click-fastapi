from pydantic import BaseModel


class ClickTransactionCreate(BaseModel):
    click_trans_id: str = ""
    service_id: str = ""
    merchant_trans_id: str = ""
    merchant_prepare_id: str = None
    amount: int
    status: str = ""
    action: str = ""
    error: str = ""
    error_note: str = ""
    sign_time: str
    sign_string: str = ""
    click_paydoc_id: str

