#!/usr/bin/env python
import sys
from automated_email_matching_and_drafting.crew import AutomatedEmailMatchingAndDraftingCrew

# This main file is intended to be a way for your to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    # Example of a realistic email for RAG (Weaviate will search by subject/body)
    new_unanswered_email = {
        'subject': 'No OTP?',
        'body': 'Cannot get OTP for South Africa?',
        'sender_name': 'Aryan'
    }
    inputs = {
        'last_1000_emails': [],  # Should be a list of email dicts if syncing
        'new_unanswered_email': new_unanswered_email,  # Pass as dict for RAG tool
        'dynamic_data': {},
        'rag_search_task': {},
        'user_email_style': 'concise and professional',
        'dynamic_data_query_task': {}
    }
    # The crew will now use Weaviate for semantic search in the RAG step
    AutomatedEmailMatchingAndDraftingCrew().crew().kickoff(inputs=inputs)


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'last_1000_emails': 'sample_value',
        'new_unanswered_email': 'sample_value',
        'dynamic_data': 'sample_value',
        'rag_search_task': 'sample_value',
        'user_email_style': 'sample_value',
        'dynamic_data_query_task': 'sample_value'
    }
    try:
        AutomatedEmailMatchingAndDraftingCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        AutomatedEmailMatchingAndDraftingCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'last_1000_emails': 'sample_value',
        'new_unanswered_email': 'sample_value',
        'dynamic_data': 'sample_value',
        'rag_search_task': 'sample_value',
        'user_email_style': 'sample_value',
        'dynamic_data_query_task': 'sample_value'
    }
    try:
        AutomatedEmailMatchingAndDraftingCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: main.py <command> [<args>]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "run":
        run()
    elif command == "train":
        train()
    elif command == "replay":
        replay()
    elif command == "test":
        test()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
