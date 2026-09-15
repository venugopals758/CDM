from django.shortcuts import render

# Create your views here.
import threading
from django.core.mail import EmailMessage


class EmailThread(threading.Thread):
    def __init__(self, subject, html_content, recipient_list, sender):
        self.subject = subject
        self.recipient_list = recipient_list
        self.html_content = html_content
        self.sender = sender
        threading.Thread.__init__(self)

    def run(self):
        sender_with_name = f"GITAM Notification <{self.sender}>"
        msg = EmailMessage(
            subject=self.subject,
            body=self.html_content,
            from_email=sender_with_name,
            to=self.recipient_list,
        )
        msg.content_subtype = 'html'
        msg.send()


def send_html_mail(subject, html_content, recipient_list, sender):
    EmailThread(subject, html_content, recipient_list, sender).start()
    #EmailThread(subject, html_content, ['kpandey@gitam.edu'], sender).start()
