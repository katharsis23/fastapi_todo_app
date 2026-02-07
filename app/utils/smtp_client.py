from app.config.config import SMTPCONFIG
import asyncio
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from loguru import logger

conf = ConnectionConfig(
    MAIL_USERNAME=SMTPCONFIG.user,
    MAIL_PASSWORD=SMTPCONFIG.password.get_secret_value(),
    MAIL_FROM=SMTPCONFIG.from_,
    MAIL_PORT=int(SMTPCONFIG.port),
    MAIL_SERVER=SMTPCONFIG.host,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


async def _send_code_verification(email: str, code: str):
    try:
        html = f"""
        <h1>Thank you for signing into Zettelkasten Notes.</h1>
        <p>Your verification key is <b>{code}</b></p>.
        <p>If it is not you, please ignore this</p>
        """
        message = MessageSchema(
            recipients=[email],
            subject="Welcome to Zettelkasten App",
            body=html,
            subtype=MessageType.html
        )
        fm = FastMail(config=conf)
        await fm.send_message(message=message)
    except Exception as error:
        logger.error(f"Error during email sending: {error}")
        return
