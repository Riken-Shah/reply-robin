import os
import weaviate
from weaviate.classes.init import Auth
from dotenv import load_dotenv
from dataclasses import asdict
from weaviate.classes.config import Configure, Property, DataType

load_dotenv()

# Best practice: store your credentials in environment variables
weaviate_url = os.environ["WEAVIATE_URL"]
weaviate_api_key = os.environ["WEAVIATE_API_KEY"]


# Recommended: save sensitive data as environment variables
openai_key = os.getenv("OPENAI_APIKEY")
headers = {
    "X-OpenAI-Api-Key": openai_key,
}


# Connect to Weaviate Cloud
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
    headers=headers
)

# print(client.is_ready())

import uuid


def retrieve_similar_emails_with_weaviate(query, top_k=5):
    """
    Retrieve similar emails from Weaviate using semantic search (RAG).
    Args:
        query (string): Body of the email to search for.
        top_k (int): Number of top similar emails to retrieve.
    Returns:
        list: Relevant emails (dicts) from Weaviate.
    """
    # Combine subject and body for search
    search_text = query.strip()
    results = client.collections.get("Email").query.near_text(
        query=search_text,
        # vector="body_vector",
        limit=top_k
    )
    # Each result is a dict with properties
    final_output = ""
    # Access results through the .objects property
    for item in results.objects:
        print(item.properties["body"])
        final_output += item.properties["reply_body"] + "\n another reply: "
    return final_output

def message_id_to_uuid(message_id: str):
    # You can use any namespace; here we use DNS for simplicity
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, message_id))

def sync_emails_to_weaviate(emails):
    """
    Sync emails to Weaviate.
    """
    if client.collections.exists("Email"):
        client.collections.delete("Email")
    client.collections.create(
        "Email",
    vectorizer_config=[
        Configure.NamedVectors.text2vec_openai(
            name="body_vector",
            source_properties=["body"]
        )
    ],
        properties=[
            Property(name="subject", data_type=DataType.TEXT),
            Property(name="body", data_type=DataType.TEXT),
            Property(name="sender", data_type=DataType.TEXT),
            Property(name="recipient", data_type=DataType.TEXT),
            Property(name="date", data_type=DataType.TEXT),
            Property(name="message_id", data_type=DataType.TEXT),
            Property(name="thread_id", data_type=DataType.TEXT),
            Property(name="reply_body", data_type=DataType.TEXT),
        ]
    )


    for email in emails:
        client.collections.get("Email").data.insert(
            uuid=message_id_to_uuid(email.message_id),
            properties=asdict(email)
        )
    print(f"Synced {len(emails)} emails to Weaviate.")