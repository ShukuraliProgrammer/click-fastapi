from tortoise import Model, fields


class ClickTransaction(Model):
    PROCESSING = 'processing'
    WAITING = "waiting"
    CONFIRMED = 'confirmed'
    CANCELED = 'canceled'
    ERROR = 'error'

    STATUS = (
        (WAITING, WAITING),
        (PROCESSING, PROCESSING),
        (CONFIRMED, CONFIRMED),
        (CANCELED, CANCELED),
        (ERROR, ERROR)
    )

    id = fields.IntField(pk=True)
    click_paydoc_id = fields.CharField(max_length=255, null=False)
    amount = fields.DecimalField(max_digits=9, decimal_places=2, default=0.0, null=False)
    action = fields.CharField(max_length=255)
    status = fields.CharField(max_length=25, choices=STATUS, default=WAITING)
    created = fields.DatetimeField(auto_now_add=True)
    modified = fields.DatetimeField(auto_now=True)
    extra_data = fields.TextField(null=True)
    message = fields.TextField(null=True)

    def __repr__(self):
        return f"<ClickTransaction(click_paydoc_id='{self.click_paydoc_id}', status='{self.status}')>"

    async def change_status(self, status: str, message=""):
        """
        Обновляет статус платежа
        """
        self.status = status
        self.message = message
        await self.save()
