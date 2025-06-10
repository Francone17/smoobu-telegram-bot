import csv
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
assistant_id = os.getenv("OPENAI_ASSISTANT_ID")


def update_assistant_instructions():
    instructions = (
        "You are an assistant that responds to guest messages using the provided document as a guide. "
        "You manage tourist apartments in Turin and assist guests with their inquiries. "
        "Please make sure you respond in the language of the guest (Italian or English) and provide helpful, accurate information based on the context of their message. "
        "Don't cite your sources by including the document reference in the response and also please don't include the name of the apartment in the response. "
        "If you have the first name of the guest please respond in a more personalized way addressing them by their first name, if you don't have it just use 'Dear Guest'."
    )

    try:
        response = client.beta.assistants.update(
            assistant_id=assistant_id,
            instructions=instructions
        )
        print("✅ Assistant instructions updated.")
    except Exception as e:
        print(f"❌ Failed to update assistant instructions: {e}")


def update_assistant_files():
    file_paths = [
        os.path.join("../data", "luggage_responses_by_apartment.txt"),
        os.path.join("../data", "prompts_chat_bot.pdf"),
        os.path.join("../data", "parking_instructions_by_apartment.txt")
    ]

    vector_store = client.vector_stores.create(name="Top Living Assistant File Store")
    file_streams = [open(path, "rb") for path in file_paths]

    try:
        file_batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=file_streams
        )

        print(f"✅ Upload complete. Status: {file_batch.status}")
        print(f"File counts: {file_batch.file_counts}")

        assistant = client.beta.assistants.update(
            assistant_id=assistant_id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
        )

        print("✅ Assistant updated with new file store.")
        print("Assistant ID:", assistant.id)

    except Exception as e:
        print(f"❌ Failed to update assistant files: {e}")

    finally:
        for f in file_streams:
            f.close()


if __name__ == "__main__":
    # Run either function here depending on your need
    update_assistant_instructions()
    update_assistant_files()
