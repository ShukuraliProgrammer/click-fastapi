
from app.click.models import ClickTransaction
from datetime import datetime

async def create_transaction(click_pydoc_id: str, amount: float, action: str, status: str) -> ClickTransaction:
    new_note = await ClickTransaction.create(
        click_paydoc_id=click_pydoc_id, amount=amount,
        action=action, status=status, extra_data="test", message="test"
    )
    print(new_note)
    return new_note

