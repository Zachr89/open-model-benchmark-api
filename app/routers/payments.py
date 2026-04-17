from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import stripe

from app.database import get_db
from app.models import User, SubscriptionTier
from app.schemas import CheckoutRequest
from app.auth import get_current_active_user
from app.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()

# Stripe Price IDs (create these in Stripe Dashboard)
PRICE_IDS = {
    SubscriptionTier.PRO: "price_pro_monthly_placeholder",  # Replace with actual Stripe Price ID
    SubscriptionTier.TEAM: "price_team_monthly_placeholder"
}


@router.post("/create-checkout-session")
def create_checkout_session(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if request.tier == SubscriptionTier.FREE:
        raise HTTPException(status_code=400, detail="Cannot checkout for free tier")
    
    if request.tier not in PRICE_IDS:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")
    
    try:
        # Create or get Stripe customer
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": current_user.id}
            )
            current_user.stripe_customer_id = customer.id
            db.commit()
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": PRICE_IDS[request.tier],
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=f"{settings.ALLOWED_ORIGINS.split(',')[0]}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.ALLOWED_ORIGINS.split(',')[0]}/cancel",
            metadata={
                "user_id": current_user.id,
                "tier": request.tier
            }
        )
        
        return {"checkout_url": checkout_session.url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/success")
def payment_success(session_id: str):
    return {"message": "Payment successful", "session_id": session_id}


@router.get("/cancel")
def payment_cancel():
    return {"message": "Payment cancelled"}
