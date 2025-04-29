import os
import json
from typing import List, Dict, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI


load_dotenv()

class APISpec(BaseModel):
    """ 
    Model representing an API specification.
    Attributes: Name (str),
                description (str), 
                endpoints (List[Dict]), 
                build_in_house (bool), 
                reason  (str)
    """
    name: str
    description: str
    endpoints: List[Dict]
    build_in_house: bool
    reason: str

class MasterplanResponse(BaseModel):
    """
    Model representing the response of the masterplan generation.
    Attributes: markdown_content (str),
                api_specs (List[APISpec]), 
                questions (Optional[List[str]])
    """
    markdown_content: str
    api_specs: List[APISpec]
    questions: Optional[List[str]] = None

class ChatOPT:
    def __init__(self):
        """
        Initialize the ChatOPT instance with the OpenAI model and define the prompts.
        The prompts are used to generate follow-up questions and the API masterplan.
        """
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.7,
            model_kwargs={"top_p": 0.9}
        )
        
        
        self.questions_prompt = PromptTemplate(
            input_variables=["mission_statement", "company_name", "industry", "business_size"],
            template="""
            You are ChatOPT, an expert in API design and software architecture. Your task is to ask follow-up questions to gather more information about the business before generating an API masterplan.
            
            Business Context:
            - Mission Statement/Operating Model: {mission_statement}
            - Company Name: {company_name}
            - Industry: {industry}
            - Business Size: {business_size}
            
            Based on this information, generate 5-7 specific questions that will help you better understand:
            1. The core business processes
            2. The users/customers and their needs
            3. Existing systems and integrations
            4. Data handling requirements
            5. Scalability and performance expectations
            6. Security and compliance requirements
            
            Format your output as a JSON list of strings containing only the questions, without any introductory text.
            """
        )
        
        self.masterplan_prompt = PromptTemplate(
            input_variables=["mission_statement", "company_name", "industry", "business_size"],
            template="""
            You are ChatOPT, an expert in API design and software architecture. Based on the business context below, create a comprehensive API masterplan.
            
            Business Context:
            - Mission Statement/Operating Model: {mission_statement}
            - Company Name: {company_name}
            - Industry: {industry}
            - Business Size: {business_size}
            
            Generate a markdown OPT (Operating Process Technology) masterplan that includes:
            
            1. Executive Summary: A brief overview of the proposed API architecture.
            
            2. Core API Specifications:
               - For each core business function, define an API with:
                 - Name and description
                 - Key endpoints (routes, methods, purpose)
                 - Data models
                 - Whether it should be built in-house or integrated with third-party services (with reasoning)
            
            3. Integration Architecture:
               - How the APIs connect with each other
               - Authentication and security considerations
               - Data flows between systems
            
            4. Implementation Roadmap:
               - Prioritized list of APIs to develop
               - Estimated complexity for each
               - Dependencies between APIs
            
            5. Technical Considerations:
               - Scalability recommendations
               - Security best practices
               - Monitoring and observability suggestions
            
            Format your response with two parts:
            1. The full markdown content for the masterplan
            2. A structured JSON array of API specifications with the following format for each API:
               ```
               {{
                 "name": "API name",
                 "description": "Brief description",
                 "endpoints": [
                   {{
                     "path": "/example/path",
                     "method": "GET|POST|PUT|DELETE",
                     "purpose": "What this endpoint does"
                   }}
                 ],
                 "build_in_house": true|false,
                 "reason": "Reasoning for build vs integrate decision"
               }}
               ```
            
            IMPORTANT: Make sure your JSON is valid and properly formatted.
            """
        )
        
        # Create the chains
        self.questions_chain = LLMChain(llm=self.llm, prompt=self.questions_prompt)
        self.masterplan_chain = LLMChain(llm=self.llm, prompt=self.masterplan_prompt)
    
    def generate_questions(self, mission_statement: str, company_name: str = None, 
                          industry: str = None, business_size: str = None) -> List[str]:
        """Generate follow-up questions based on the initial business information
           Returns a list of questions to gather more information
        """
        try:
            response = self.questions_chain.run({
                "mission_statement": mission_statement,
                "company_name": company_name or "Not specified",
                "industry": industry or "Not specified",
                "business_size": business_size or "Not specified"
            })
            
            # Parse the JSON response
            try:
                questions = json.loads(response)
                if isinstance(questions, list):
                    return questions
                return ["Could not generate questions. Please try again."]
            except json.JSONDecodeError:
                # If not valid JSON, try to extract questions from the text
                lines = [line.strip() for line in response.strip().split('\n') 
                         if line.strip() and not line.strip().startswith('[') and not line.strip().endswith(']')]
                if lines:
                    return lines
                return ["Could not generate questions. Please try again."]
                
        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            return ["An error occurred while generating questions. Please try again."]
    
    def generate_masterplan(self, mission_statement: str, company_name: str = None,
                           industry: str = None, business_size: str = None) -> MasterplanResponse:
        """
        Generate the API masterplan based on the business information
        Returns a MasterplanResponse object containing the markdown content and API specs
        """
        try:
            response = self.masterplan_chain.run({
                "mission_statement": mission_statement,
                "company_name": company_name or "Not specified",
                "industry": industry or "Not specified",
                "business_size": business_size or "Not specified"
            })
            
            # Extract the markdown content and API specs JSON
            markdown_content = response
            api_specs = []
            
            # Try to find and parse the JSON part
            try:
                # Look for JSON array pattern
                import re
                json_match = re.search(r'\[\s*{\s*"name":', response)
                if json_match:
                    json_start = json_match.start()
                    json_content = response[json_start:]
                    # Find the closing bracket for the array
                    bracket_count = 0
                    for i, char in enumerate(json_content):
                        if char == '[':
                            bracket_count += 1
                        elif char == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                json_content = json_content[:i+1]
                                break
                    
                    api_specs_raw = json.loads(json_content)
                    api_specs = [APISpec(**spec) for spec in api_specs_raw]
                    
                    # Remove the JSON part from the markdown content
                    markdown_content = response[:json_start].strip()
                
                # If no JSON found in expected format, return just the markdown
                return MasterplanResponse(
                    markdown_content=markdown_content,
                    api_specs=api_specs
                )
                
            except (json.JSONDecodeError, ValueError) as e:
                # If JSON parsing fails, return just the markdown
                print(f"Error parsing API specs JSON: {str(e)}")
                return MasterplanResponse(
                    markdown_content=markdown_content,
                    api_specs=[]
                )
                
        except Exception as e:
            print(f"Error generating masterplan: {str(e)}")
            return MasterplanResponse(
                markdown_content=f"An error occurred while generating the masterplan: {str(e)}",
                api_specs=[]
            ) 