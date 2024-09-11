# app/email.py

from flask_mail import Message
from flask import render_template
from app import mail

def send_tentative_email(to, recipient_name):
    msg = Message(subject="Booking Tentative",
                  recipients=[to],
                  html=render_template('emails/tentative_email.html', recipient_name=recipient_name))
    
    mail.send(msg)

def send_confirmation_email(to, recipient_name, confirmation_number):
    msg = Message(subject="Booking Confirmation",
                  recipients=[to],
                  html=render_template('emails/confirmation_email.html', recipient_name=recipient_name, confirmation_number=confirmation_number))
    mail.send(msg)

def send_invoice_paid_email(to, recipient_name):
    msg = Message(subject="Invoice Payment Confirmation",
                  recipients=[to],
                  html=render_template('emails/invoice_paid_email.html', recipient_name=recipient_name))
    mail.send(msg)
