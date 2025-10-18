"""
Stripe Payment Service
Handles payment processing with Stripe Checkout
Supports deferred capture and promotional codes
"""

import json
import logging
import stripe
import time
import os

logger = logging.getLogger(__name__)

# Initialize Stripe with API key from environment
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


def create_checkout_session(
    job_id: str,
    amount_eur_cents: int,
    customer_email: str | None,
    locale: str,
    success_url: str,
    cancel_url: str,
    promotion_code: str | None = None
):
    """
    Create a Stripe Checkout session with promo code support.

    This function creates a payment session that:
    - Supports automatic promo codes
    - Expires after 30 minutes
    - Includes job metadata for webhook processing

    Args:
        job_id: Unique job identifier
        amount_eur_cents: Amount in euro cents (e.g., 990 = 9.90€)
        customer_email: Customer's email address
        locale: Language locale (fr/en)
        success_url: Redirect URL after successful payment
        cancel_url: Redirect URL on cancellation
        promotion_code: Specific promo code to apply (optional)

    Returns:
        Stripe Session object with payment URL
    """

    # Calculate units for display (each unit = 10 seconds)
    units = amount_eur_cents // 100  # Number of 10-second units
    duration_seconds = units * 10

    logger.info(f"Creating Stripe session: {amount_eur_cents} cents → {units} units → {duration_seconds}s")

    # Session expires after 30 minutes (instead of default 24h)
    expires_at = int(time.time()) + 1800

    session_params = {
        "mode": "payment",
        "payment_method_types": ["card"],
        "expires_at": expires_at,
        "client_reference_id": job_id,  # CRITICAL: Used in webhook to identify job

        "payment_intent_data": {
            "capture_method": "automatic",  # Auto-capture after payment
            "description": f"Video animation - {duration_seconds} seconds",
            "statement_descriptor": "PICTURETOFILM",  # Shown on bank statement
        },

        "line_items": [{
            "price_data": {
                "currency": "eur",
                "product_data": {
                    "name": f"Video animation ({duration_seconds}s)" if locale == "en" else f"Animation vidéo ({duration_seconds}s)",
                    "description": f"✨ {units} unit(s) of 10 seconds - Delivery in 2-3 minutes" if locale == "en" else f"✨ {units} unité(s) de 10 secondes - Livraison en 2-3 minutes",
                },
                "unit_amount": amount_eur_cents,
            },
            "quantity": 1
        }],

        "customer_email": customer_email,
        "locale": locale if locale in ["fr", "en", "es", "de", "it", "pt"] else "en",
        "success_url": success_url,
        "cancel_url": cancel_url,

        "metadata": {
            "job_id": job_id,
            "duration_seconds": str(duration_seconds),
            "units": str(units)
        },

        "submit_type": "pay",
    }

    # Handle promotional codes
    if promotion_code:
        # Apply specific promo code if provided
        try:
            promo_codes = stripe.PromotionCode.list(
                code=promotion_code,
                active=True,
                limit=1
            )
            if promo_codes.data:
                session_params["discounts"] = [{"promotion_code": promo_codes.data[0].id}]
                logger.info(f"Promo code '{promotion_code}' applied for job {job_id}")
            else:
                logger.warning(f"Promo code '{promotion_code}' not found or inactive")
        except Exception as e:
            logger.error(f"Error applying promo code: {e}")
    else:
        # Allow users to enter promo codes in Stripe Checkout UI
        session_params["allow_promotion_codes"] = True

    # Create and return session
    session = stripe.checkout.Session.create(**session_params)
    logger.info(f"Stripe session created: {session.id}")
    return session


def retrieve_checkout_session(session_id: str):
    """
    Retrieve a Stripe Checkout session by ID
    """
    return stripe.checkout.Session.retrieve(session_id)


def capture_payment(payment_intent_id: str):
    """
    Capture a previously authorized payment
    Used for manual capture flow (if needed)
    """
    return stripe.PaymentIntent.capture(payment_intent_id)


def cancel_payment(payment_intent_id: str):
    """
    Cancel a payment intent
    Used when generation fails before capture
    """
    return stripe.PaymentIntent.cancel(payment_intent_id)


def refund_payment(payment_intent_id: str, amount_cents: int | None = None):
    """
    Issue a refund for a captured payment

    Args:
        payment_intent_id: Stripe PaymentIntent ID
        amount_cents: Amount to refund in cents (None = full refund)
    """
    refund_params = {"payment_intent": payment_intent_id}
    if amount_cents:
        refund_params["amount"] = amount_cents

    return stripe.Refund.create(**refund_params)


def construct_event_from_request(payload: bytes, sig_header: str):
    """
    Construct and verify a Stripe webhook event

    This function:
    1. Verifies the webhook signature (in production)
    2. Constructs the event object from the payload
    3. Returns the verified event for processing

    Args:
        payload: Raw request body bytes
        sig_header: Stripe-Signature header value

    Returns:
        Verified Stripe Event object

    Raises:
        stripe.error.SignatureVerificationError: Invalid signature
    """
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    if not webhook_secret:
        # In development, parse without signature verification
        logger.warning("STRIPE_WEBHOOK_SECRET not set - skipping signature verification")
        return stripe.Event.construct_from(
            json.loads(payload.decode("utf-8")),
            stripe.api_key
        )

    # Verify webhook signature in production
    return stripe.Webhook.construct_event(
        payload=payload,
        sig_header=sig_header,
        secret=webhook_secret
    )


def list_promotion_codes(active_only: bool = True):
    """
    List all promotion codes configured in Stripe

    Args:
        active_only: Only return active codes

    Returns:
        List of promotion codes
    """
    return stripe.PromotionCode.list(active=active_only, limit=100)


def get_payment_intent(payment_intent_id: str):
    """
    Retrieve a payment intent by ID

    Args:
        payment_intent_id: Stripe PaymentIntent ID

    Returns:
        PaymentIntent object with full details
    """
    return stripe.PaymentIntent.retrieve(payment_intent_id)


# Pricing configuration (in cents)
PRICING_EUR_CENTS = {
    "5": 490,    # 4.90€ for 5 seconds
    "10": 690,   # 6.90€ for 10 seconds
    "20": 990,   # 9.90€ for 20 seconds
    "30": 1490,  # 14.90€ for 30 seconds
    "60": 2490,  # 24.90€ for 60 seconds
}


def calculate_price(duration_seconds: int) -> int:
    """
    Calculate price based on video duration

    Args:
        duration_seconds: Video duration in seconds

    Returns:
        Price in euro cents
    """
    duration_str = str(duration_seconds)
    return PRICING_EUR_CENTS.get(duration_str, PRICING_EUR_CENTS["20"])  # Default to 20s pricing