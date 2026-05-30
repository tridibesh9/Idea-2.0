import re
from app.services.email_parser import extract_ticket_id_from_subject

subjects = [
    "[Ticket #01080ce5-f1e8-4a5b-817c-da191bee9c59] Re: Hello",
    "Re: [Ticket #01080ce5-f1e8-4a5b-817c-da191bee9c59] Hello",
    "Fwd: [Ticket #01080ce5-f1e8-4a5b-817c-da191bee9c59]"
]

for s in subjects:
    print(f"{s} -> {extract_ticket_id_from_subject(s)}")
