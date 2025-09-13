import stripe
import os

stripe.api_key = os.getenv("STRIPE_API_KEY")

def create_checkout_session(appointment_id: int, doctor_name: str, amount: float, success_url: str, cancel_url: str):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'unit_amount': int(amount * 100),  # Stripe expects cents
                'product_data': {'name': f'Appointment with Dr. {doctor_name}'},
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}&appointment_id={appointment_id}",
        cancel_url=cancel_url,
    )
    return session
