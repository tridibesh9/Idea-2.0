import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from app.services.email_parser import ParsedEmail, extract_text_from_html
from app.services.email_listener import process_parsed_email

router = APIRouter()
logger = logging.getLogger("webhooks")

@router.post("/resend/inbound")
async def resend_inbound_webhook(request: Request, background_tasks: BackgroundTasks):
    """Webhook for Resend inbound emails."""
    try:
        payload = await request.json()
        
        # Resend webhook wraps the email payload in 'data'
        # Wait, if you setup webhooks for 'email.received', type is 'email.received'
        # Sometimes people don't use the wrapper and just post direct.
        # Let's support both unwrapped and wrapped
        if "data" in payload and "type" in payload:
            if payload.get("type") != "email.received":
                return {"status": "ignored"}
            data = payload["data"]
        else:
            data = payload
            
        # Parse fields
        from_field = data.get("from", "")
        # Handle 'Name <email@example.com>' or just 'email@example.com'
        from_email = from_field
        from_name = from_field
        if "<" in from_field and ">" in from_field:
            from_name = from_field.split("<")[0].strip()
            from_email = from_field.split("<")[1].split(">")[0].strip()
            
        subject = data.get("subject", "No Subject")
        
        text = data.get("text", "")
        html = data.get("html", "")
        if not text and html:
            text = extract_text_from_html(html)
            
        headers = data.get("headers", {})
        message_id = headers.get("Message-ID", "") or data.get("message_id", "")
        in_reply_to = headers.get("In-Reply-To", "")
        references_str = headers.get("References", "")
        references = references_str.split() if references_str else []
        
        parsed = ParsedEmail(
            from_email=from_email,
            from_name=from_name,
            subject=subject,
            body_text=text,
            body_html=html,
            date=datetime.now(timezone.utc),
            message_id=message_id,
            in_reply_to=in_reply_to,
            references=references
        )
        
        from app.routes.websocket import manager
        async def broadcast_email(msg_data):
            try:
                await manager.broadcast(msg_data)
            except Exception as e:
                logger.warning(f"Failed to broadcast: {e}")
                
        # Run in background to reply 200 OK to Resend immediately
        background_tasks.add_task(process_parsed_email, parsed, broadcast_email)
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Error handling Resend webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
