from flask import url_for, render_template
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message


class Smt:
    def __init__(
        self,
        db,
        resend,
        reset,
        server,
        mail,
        access: str = "",
        data: str = "",
        username: str = ""
    ):

        self.db = db
        self.resend = resend
        self.reset = reset
        self.server = server
        self.mail = mail
        self.data = data
        self.access = access
        self.username = username
        self.send_error: str = "There's an error while sending the email, please try again"

    def authentication(self) -> str:

        confirm_serializer = URLSafeTimedSerializer(
            self.server.config["SECRET_KEY"])
        confirm_url = url_for(self.access, token=confirm_serializer.dumps(
            self.data, salt=self.server.config["SECURITY_PASSWORD_SALT"]), _external=True)

        return confirm_url

    def send(self) -> None | dict:
        try:
            confirm_url = self.authentication()

            resend_token = self.resend(
                token=confirm_url.split("verification/")[1])

            self.db.session.add(resend_token)
            self.db.session.commit()

            template = render_template(
                "email_content.html", data=[confirm_url, self.username])

            msg: Message = Message(
                recipients=[self.data], subject="Verify your Email", html=template)

            self.mail.send(msg)

        except Exception:
            return {"error": self.send_error}

    def request(self) -> None | dict:
        try:
            confirm_url = self.authentication()

            reset_token = self.reset(
                token=confirm_url.split("confirm_reset/")[1])

            self.db.session.add(reset_token)
            self.db.session.commit()

            template = render_template(
                "request_password.html", data=[confirm_url, self.username])

            msg: Message = Message(
                recipients=[self.data], subject="Request a new Password", html=template)

            self.mail.send(msg)

        except Exception:
            return {"error": self.send_error}
