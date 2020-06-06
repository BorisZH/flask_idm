import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import json


class MailSender:
    def __init__(self, config_path):
        self._config = json.load(open(config_path, 'r'))

    def send_mail(self, 
                to_addrs, 
                subject, 
                msg_text, 
                use_sign=True, 
                sign='Отправлено системой автоматических уведомлений. \nБорис Жестков',
                attachments_fp=None):
        msg = MIMEMultipart()
        msg.attach(MIMEText(msg_text + '\n\n\n' + sign if use_sign else msg_text))
        msg['Subject'] = subject
        msg['From'] = self._config['MAIL_USER']
        msg['To'] = ', '.join(to_addrs)

        if attachments_fp is not None:
            attachments_fp = attachments_fp if isinstance(attachments_fp, list) else [attachments_fp]
            for fp in attachments_fp:
                with open(fp, "rb") as f:
                    attach = MIMEApplication(
                        f.read(),
                        Name=basename(fp),
                    )
                attach['Content-Disposition'] = 'attachment; filename="{}"'.format(basename(fp))
                msg.attach(attach)
        server = smtplib.SMTP_SSL(host=self._config['SMTP_HOST'], port=self._config['SMTP_PORT'])
        server.login(self._config['MAIL_USER'], self._config['MAIL_PWD'])
        server.sendmail(msg=msg.as_string(), to_addrs=to_addrs, from_addr=self._config['MAIL_USER'])
        server.quit()
