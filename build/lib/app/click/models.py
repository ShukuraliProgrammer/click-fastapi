import enum

class ClickStatusEnum(str, enum.Enum):
    PROCESSING = 'processing'
    WAITING = "waiting"
    CONFIRMED = 'confirmed'
    CANCELED = 'canceled'
    ERROR = 'error'

class ClickTransaction(BaseModel):
    """ Класс ClickTransaction """
    click_trans_id = db.Column(db.String)
    merchant_trans_id = db.Column(db.String)
    merchant_prepare_id = db.Column(db.String)
    sign_string = db.Column(db.String)
    sign_datetime = db.Column(db.String)
    click_paydoc_id = db.Column(db.String, comment="Номер платежа в системе CLICK")
    amount = db.Column(db.DECIMAL(precision=12, scale=2, asdecimal=False), comment="Сумма оплаты (в сумах)")
    action = db.Column(db.String, comment="Выполняемое действие")
    status = db.Column(Enum(ClickStatusEnum), default=ClickStatusEnum.WAITING)
    extra_data = db.Column(db.String)
    message = db.Column(db.Text)
    created_by_id = db.Column(UUID, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    created_by = relationship("User", backref=backref("click_transaction", cascade="all,delete"), lazy="selectin")