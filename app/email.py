# app/email.py

from flask_mail import Message
from flask import render_template
from app import mail

def send_tentative_email(to, recipient_name, agency_name, destination, check_in, check_out, booking_ref, hotel_name, 
                         agent_ref, hotel_address, nights, num_of_rooms, room_type, inclusion, notes, guests, total_price):
   
    msg = Message(
        subject="Booking Tentative",
        recipients=[to],
        html=render_template(
            'emails/tentative_email.html',
            recipient_name=recipient_name,
            agency_name=agency_name,
            destination=destination,
            check_in=check_in,
            check_out=check_out,
            booking_ref=booking_ref,
            hotel_name=hotel_name,
            agent_ref=agent_ref,
            hotel_address=hotel_address,
            nights=nights,
            num_of_rooms=num_of_rooms,
            room_type=room_type,
            inclusion=inclusion,
            notes=notes,
            guests=guests,
            total_price=total_price
        )
    )
    mail.send(msg)

def send_confirmation_email(to, recipient_name, agency_name, destination, check_in, check_out, booking_ref, hotel_name, 
                         agent_ref, hotel_address, nights, num_of_rooms, room_type, inclusion, notes, guests, total_price, confirmation_number):
   
    msg = Message(
        subject="Booking Confirmation",
        recipients=[to],
        html=render_template(
            'emails/confirmation_email.html',
            recipient_name=recipient_name,
            agency_name=agency_name,
            destination=destination,
            check_in=check_in,
            check_out=check_out,
            booking_ref=booking_ref,
            hotel_name=hotel_name,
            agent_ref=agent_ref,
            hotel_address=hotel_address,
            nights=nights,
            num_of_rooms=num_of_rooms,
            room_type=room_type,
            inclusion=inclusion,
            notes=notes,
            guests=guests,
            total_price=total_price,
            hcn= confirmation_number
        )
    )
    mail.send(msg)

def send_tcn_confirmation_email(to, recipient_name, agency_name, destination, check_in, check_out, booking_ref, hotel_name, 
                         agent_ref, hotel_address, nights, num_of_rooms, room_type, inclusion, notes, guests, total_price, confirmation_number):
   
    msg = Message(
        subject="Times Booking Confirmation",
        recipients=[to],
        html=render_template(
            'emails/tcn_confirmation_email.html',
            recipient_name=recipient_name,
            agency_name=agency_name,
            destination=destination,
            check_in=check_in,
            check_out=check_out,
            booking_ref=booking_ref,
            hotel_name=hotel_name,
            agent_ref=agent_ref,
            hotel_address=hotel_address,
            nights=nights,
            num_of_rooms=num_of_rooms,
            room_type=room_type,
            inclusion=inclusion,
            notes=notes,
            guests=guests,
            total_price=total_price,
            hcn= confirmation_number
        )
    )
    mail.send(msg)


def send_invoice_paid_email(to, recipient_name, agency_name, destination, check_in, check_out, booking_ref, hotel_name, 
                         agent_ref, hotel_address, nights, num_of_rooms, room_type, inclusion, notes, guests, total_price,
                         invoice_id, invoice_date, invoice_time):
    msg = Message(subject=f"Invoice for Booking { booking_ref }",
                  recipients=[to],
                  html=render_template
                  ('emails/invoice_paid_email.html',
                    recipient_name=recipient_name,
                    agency_name=agency_name,
                    destination=destination,
                    check_in=check_in,
                    check_out=check_out,
                    booking_ref=booking_ref,
                    hotel_name=hotel_name,
                    agent_ref=agent_ref,
                    hotel_address=hotel_address,
                    nights=nights,
                    num_of_rooms=num_of_rooms,
                    room_type=room_type,
                    inclusion=inclusion,
                    notes=notes,
                    guests=guests,
                    total_price=total_price,
                    invoice_id=invoice_id, 
                    invoice_date=invoice_date,
                    invoice_time=invoice_time
        ))
    mail.send(msg)

def send_booking_reservation_status(to, recipient_name, agency_name, check_in, check_out, hotel_name, room_requests, status,confirmation_link): 
    msg = Message(subject=f"Status for Booking Request",
                  recipients=[to],
                  html=render_template
                  ('emails/booking_reservation_status.html',
                    recipient_name=recipient_name,
                    agency_name=agency_name,
                    check_in=check_in,
                    check_out=check_out,
                    hotel_name=hotel_name,
                    room_requests = room_requests,
                    status = status,
                    confirmation_link = confirmation_link
        ))
    mail.send(msg)
 
    
def send_invoice_email(to, recipient_name, agency_name, destination, check_in, check_out, booking_ref, hotel_name, 
                         agent_ref, hotel_address, nights, num_of_rooms, room_type, inclusion, notes, guests, total_price):
    msg = Message(subject=f"Invoice for Booking { booking_ref }",
                  recipients=[to],
                  html=render_template
                  ('emails/invoice_email.html',
                    recipient_name=recipient_name,
                    agency_name=agency_name,
                    destination=destination,
                    check_in=check_in,
                    check_out=check_out,
                    booking_ref=booking_ref,
                    hotel_name=hotel_name,
                    agent_ref=agent_ref,
                    hotel_address=hotel_address,
                    nights=nights,
                    num_of_rooms=num_of_rooms,
                    room_type=room_type,
                    inclusion=inclusion,
                    notes=notes,
                    guests=guests,
                    total_price=total_price
        ))
    mail.send(msg)