import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

def get_assistant_response(message: str, reservation: dict, guest_name: str, apt_name: str) -> str:
    """
    Sends a message and reservation context to the OpenAI Assistant
    and returns the assistant's response.

    Args:
        guest_name:
    """
    thread = client.beta.threads.create()

    content = f"User message: {message}\nGuest name: {guest_name}\nApartment name: {apt_name}\n\n"
    print(content)

    # Add user message
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=content
    )

    # Run the assistant with extra instructions/context
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
        additional_instructions=format_reservation_context(reservation)
    )

    # Wait for run to complete (polling)
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        elif run_status.status in {"failed", "cancelled", "expired"}:
            raise Exception(f"Run failed with status: {run_status.status}")
        time.sleep(1)  # Poll every second

    # Get assistant's response
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for msg in reversed(messages.data):
        if msg.role == "assistant":
            return msg.content[0].text.value.strip()

    return "Sorry, I couldn't generate a response."

def format_reservation_context(reservation: dict) -> str:
    """
    Format reservation details as context for the assistant.
    You can customize this based on what the assistant needs to know.
    """
    guest_name = reservation.get("guestName", "Guest")
    checkin = reservation.get("arrival", "N/A")
    checkout = reservation.get("departure", "N/A")
    apartment = reservation.get("apartmentName", "N/A")

    return (
        f"You're helping respond to a guest named {guest_name}.\n"
        f"Their reservation is for apartment '{apartment}' from {checkin} to {checkout}.\n"
        f"Please be polite, concise, and helpful in your reply."
    )
