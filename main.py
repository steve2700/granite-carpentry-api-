from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

app = FastAPI(title="Granite Joinery Quote API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://granitecarpentry.co.za/"],  # Add your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")  # Your email
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # Your email password/app password
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")  # Where to send notifications

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and Key must be provided")

if not SMTP_USERNAME or not SMTP_PASSWORD or not ADMIN_EMAIL:
    print("Warning: Email credentials not provided. Email notifications disabled.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class QuoteRequest(BaseModel):
    name: str
    phone: str
    email: EmailStr
    location: str
    service: str
    budget: Optional[str] = None
    timeline: Optional[str] = None
    message: str
    consultation: bool = False
    updates: bool = False
    privacy: bool

class QuoteResponse(BaseModel):
    id: str
    message: str
    status: str

@app.get("/")
async def root():
    return {"message": "Granite Joinery Quote API is running"}

async def send_email_notification(quote_data: dict):
    """Send email notification when new quote is submitted"""
    try:
        if not all([SMTP_USERNAME, SMTP_PASSWORD, ADMIN_EMAIL]):
            print("Email credentials not configured, skipping email notification")
            return
        
        # Create email content
        subject = f"🔨 New Quote Request from {quote_data['name']}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #d97706 0%, #b45309 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">🔨 New Quote Request</h1>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Granite Joinery Experts</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border: 1px solid #e9ecef;">
                    <h2 style="color: #d97706; margin-top: 0;">Customer Details</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; width: 120px;">Name:</td>
                            <td style="padding: 8px 0;">{quote_data['name']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Phone:</td>
                            <td style="padding: 8px 0;"><a href="tel:{quote_data['phone']}" style="color: #d97706;">{quote_data['phone']}</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Email:</td>
                            <td style="padding: 8px 0;"><a href="mailto:{quote_data['email']}" style="color: #d97706;">{quote_data['email']}</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Location:</td>
                            <td style="padding: 8px 0;">{quote_data['location']}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background: white; padding: 20px; border: 1px solid #e9ecef; border-top: none;">
                    <h2 style="color: #d97706; margin-top: 0;">Project Information</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; width: 120px;">Service:</td>
                            <td style="padding: 8px 0;">{quote_data['service']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Budget:</td>
                            <td style="padding: 8px 0;">{quote_data['budget'] or 'Not specified'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Timeline:</td>
                            <td style="padding: 8px 0;">{quote_data['timeline'] or 'Not specified'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Consultation:</td>
                            <td style="padding: 8px 0;">{'✅ Yes' if quote_data['consultation_requested'] else '❌ No'}</td>
                        </tr>
                    </table>
                    
                    <h3 style="color: #d97706; margin-top: 25px;">Project Details:</h3>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #d97706;">
                        <p style="margin: 0; white-space: pre-wrap;">{quote_data['message']}</p>
                    </div>
                </div>
                
                <div style="background: #d97706; color: white; padding: 20px; border-radius: 0 0 10px 10px; text-align: center;">
                    <p style="margin: 0;"><strong>⏰ Remember:</strong> Respond within 24 hours for best results!</p>
                    <div style="margin-top: 15px;">
                        <a href="tel:{quote_data['phone']}" style="background: white; color: #d97706; padding: 8px 16px; text-decoration: none; border-radius: 5px; margin: 0 5px; font-weight: bold;">📞 Call Now</a>
                        <a href="mailto:{quote_data['email']}" style="background: white; color: #d97706; padding: 8px 16px; text-decoration: none; border-radius: 5px; margin: 0 5px; font-weight: bold;">✉️ Email</a>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                    <p>Quote submitted on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_USERNAME
        msg['To'] = ADMIN_EMAIL
        
        # Add HTML content
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"Email notification sent successfully to {ADMIN_EMAIL}")
        
    except Exception as e:
        print(f"Failed to send email notification: {str(e)}")
        # Don't raise exception - email failure shouldn't break the API

@app.post("/api/quote", response_model=QuoteResponse)
async def submit_quote(quote: QuoteRequest):
    try:
        # Validate privacy agreement
        if not quote.privacy:
            raise HTTPException(status_code=400, detail="Privacy policy agreement is required")
        
        # Prepare data for Supabase
        quote_data = {
            "name": quote.name,
            "phone": quote.phone,
            "email": quote.email,
            "location": quote.location,
            "service": quote.service,
            "budget": quote.budget,
            "timeline": quote.timeline,
            "message": quote.message,
            "consultation_requested": quote.consultation,
            "marketing_updates": quote.updates,
            "privacy_agreed": quote.privacy,
            "created_at": datetime.utcnow().isoformat(),
            "status": "new"
        }
        
        # Insert into Supabase
        result = supabase.table("quotes").insert(quote_data).execute()
        
        if result.data:
            # Send email notification
            await send_email_notification(quote_data)
            
            return QuoteResponse(
                id=result.data[0]["id"],
                message="Quote request submitted successfully! We'll respond within 24 hours.",
                status="success"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to submit quote request")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/quotes")
async def get_quotes():
    """Admin endpoint to get all quotes"""
    try:
        result = supabase.table("quotes").select("*").order("created_at", desc=True).execute()
        return {"quotes": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch quotes: {str(e)}")

@app.get("/api/quotes/{quote_id}")
async def get_quote(quote_id: str):
    """Get a specific quote by ID"""
    try:
        result = supabase.table("quotes").select("*").eq("id", quote_id).execute()
        if result.data:
            return {"quote": result.data[0]}
        else:
            raise HTTPException(status_code=404, detail="Quote not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch quote: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
