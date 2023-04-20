import hashlib
import datetime

from app.config import settings


def authorization(click_trans_id: str,
                  amount: int,
                  action: str,
                  sign_time: datetime.datetime,
                  sign_string: str,
                  merchant_trans_id: str,
                  merchant_prepare_id: str = None,
                  *args, **kwargs) -> bool:
    """
    Authorization
    :param click_trans_id:
    :param amount:
    :param action:
    :param sign_time:
    :param sign_string:
    :param merchant_trans_id:
    :param merchant_prepare_id:
    :return: bool
    """
    print("ssdd: ", settings.CLICK_SETTINGS.get('service_id', None))

    assert settings.CLICK_SETTINGS.get('service_id', None)
    assert settings.CLICK_SETTINGS.get('secret_key', None)
    assert settings.CLICK_SETTINGS.get('merchant_user_id', None)

    service_id = settings.CLICK_SETTINGS['service_id']
    secret_key = settings.CLICK_SETTINGS['secret_key']
    print("Step 1: ", service_id, secret_key)
    text = f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}"
    if merchant_prepare_id != "" and merchant_prepare_id is not None:
        text += f"{merchant_prepare_id}"
    print("Step 2: ", text)
    text += f"{amount}{action}{sign_time}"
    encoded_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    print("Step 3: ", encoded_hash)
    if encoded_hash != sign_string:
        print("Step 4: ", encoded_hash, sign_string)
        return True
    return False
