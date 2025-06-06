import csv
import os
from openai import OpenAI

# Load env vars
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
assistant_id = os.getenv("OPENAI_ASSISTANT_ID")


def create_assistant_with_file():
    assistant = client.beta.assistants.create(
        name="Top Living Assistant",
        instructions="You are a helpful assistant who responds to guest messages using the provided document as a guide.",
        model="gpt-4o",
        tools=[{"type": "file_search"}],
    )
    file_paths = [
        os.path.join("../data", "luggage_responses_by_apartment.csv"),
        os.path.join("../data", "prompts_chat_bot.pdf"),
        os.path.join("../data", "parking_instructions_by_apartment.csv")
    ]

    print(assistant.id)

    # Create a new vector store
    vector_store = client.vector_stores.create(name="Top Living Assistant File Store")

    # Open all files as binary streams
    file_streams = [open(path, "rb") for path in file_paths]

    file_batch = client.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )

    # You can print the status and the file counts of the batch to see the result of this operation.
    print(file_batch.status)
    print(file_batch.file_counts)


    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )

    print("✅ Assistant created successfully.")
    print("Assistant ID:", assistant.id)


def update_assistant_file():
    file_paths = [
        os.path.join("../data", "luggage_responses_by_apartment.txt"),
        os.path.join("../data", "prompts_chat_bot.pdf"),
        os.path.join("../data", "parking_instructions_by_apartment.txt")
    ]

    # Create a new vector store
    vector_store = client.vector_stores.create(name="Top Living Assistant File Store")

    # Open all files as binary streams
    file_streams = [open(path, "rb") for path in file_paths]

    print(f"files opened successfully. {vector_store.id}")

    try:
        # Upload all files in one batch
        file_batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=file_streams
        )

        print(f"Upload status: {file_batch.status}")
        print(f"File counts: {file_batch.file_counts}")

        # Update the assistant with this new vector store
        assistant = client.beta.assistants.update(
            assistant_id=assistant_id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
        )

        print("✅ Assistant updated successfully.")
        print("Assistant ID:", assistant.id)

    finally:
        # Always close file streams
        for f in file_streams:
            f.close()


def update_assistant_instructions(assistant_id: str, new_instructions: str) -> dict:
    try:
        response = client.beta.assistants.update(
            assistant_id=assistant_id,
            instructions=new_instructions
        )
        print("✅ Assistant instructions updated.")
        return response
    except Exception as e:
        print(f"❌ Failed to update assistant instructions: {e}")
        return None


def list_files():
    assistant = client.beta.assistants.retrieve(assistant_id)
    print(assistant.file_ids)


def csv_to_txt(csv_path, txt_path):
    with open(csv_path, "r", encoding="utf-8") as csv_file, \
         open(txt_path, "w", encoding="utf-8") as txt_file:
        reader = csv.reader(csv_file)
        for row in reader:
            txt_file.write(" | ".join(row) + "\n")


if __name__ == "__main__":
    update_assistant_instructions(
        assistant_id=assistant_id,
        new_instructions="You are an assistant that responds to guest messages using the provided document as a guide."
                         "You manage tourist apartments in Turin and assist guests with their inquiries."
                         "Please make sure you respond in the language of the guest (Italian or English) and provide helpful, accurate information based on the context of their message."
    )
