from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import JSONSearchTool
from automated_email_matching_and_drafting.emd import retrieve_similar_emails_with_weaviate

from crewai.tools import tool

@tool("Weaviate RAG Tool")
def weaviate_rag_tool(query: dict) -> str:
    """Tool description for clarity."""
    # Tool logic here
    print(query['description'])
    return retrieve_similar_emails_with_weaviate(query['description'])

@tool("Ask Question Using CLI")
def ask_question_using_cli(question: str) -> str:
    """Tool description for clarity."""
    # Tool logic here
    print(question)
    ans = input("Answer: ")
    return ans

@CrewBase
class AutomatedEmailMatchingAndDraftingCrew():
    """AutomatedEmailMatchingAndDrafting crew"""

    @agent
    def rag_search_expert(self) -> Agent:
        return Agent(
            config=self.agents_config['rag_search_expert'],
            tools=[weaviate_rag_tool],
        )

    @agent
    def dynamic_data_inquirer(self) -> Agent:
        return Agent(
            config=self.agents_config['dynamic_data_inquirer'],
            tools=[ask_question_using_cli],
        )

    @agent
    def email_draft_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['email_draft_generator'],
            tools=[],
        )


    @task
    def rag_search_task(self) -> Task:
        return Task(
            config=self.tasks_config['rag_search_task'],
            tools=[weaviate_rag_tool],
        )

    @task
    def dynamic_data_query_task(self) -> Task:
        return Task(
            config=self.tasks_config['dynamic_data_query_task'],
            tools=[ask_question_using_cli],
        )

    @task
    def email_drafting_task(self) -> Task:
        return Task(
            config=self.tasks_config['email_drafting_task'],
            tools=[],
        )


    @crew
    def crew(self) -> Crew:
        """Creates the AutomatedEmailMatchingAndDrafting crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
