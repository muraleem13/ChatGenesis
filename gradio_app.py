import gradio as gr
import requests
import json
from typing import List, Dict

# API endpoint URL (change if needed)
API_URL = "http://localhost:8000"

def ask_questions(mission_statement: str, company_name: str, industry: str, business_size: str) -> List[str]:
    """
    Get follow-up questions based on the initial information provided.
    """
    payload = {
        "mission_statement": mission_statement,
        "company_name": company_name if company_name else None,
        "industry": industry if industry else None,
        "business_size": business_size if business_size else None
    }
    
    response = requests.post(f"{API_URL}/ask_questions", json=payload)
    if response.status_code == 200:
        return response.json().get("questions", [])
    else:
        return ["Error: Could not generate questions. Please try again."]

def generate_masterplan(
    mission_statement: str, 
    company_name: str, 
    industry: str, 
    business_size: str,
    answers: str
) -> str:
    """
    Generate the OPT masterplan
    based on the mission statement and additional information provided.
    """
    try:
        # Combine mission statement with answers
        full_mission = f"{mission_statement}\n\nAdditional Information:\n{answers}"
        
        payload = {
            "mission_statement": full_mission,
            "company_name": company_name if company_name else None,
            "industry": industry if industry else None,
            "business_size": business_size if business_size else None
        }
        
        response = requests.post(f"{API_URL}/generate_masterplan", json=payload)
        if response.status_code == 200:
            data = response.json()
            markdown_content = data.get("markdown_content", "")
            
            # Format API specifications if available
            api_specs = data.get("api_specs", [])
            if api_specs:
                markdown_content += "\n\n## API Specifications\n\n"
                for spec in api_specs:
                    markdown_content += f"### {spec['name']}\n"
                    markdown_content += f"{spec['description']}\n\n"
                    markdown_content += "**Endpoints:**\n"
                    for endpoint in spec['endpoints']:
                        markdown_content += f"- `{endpoint['method']} {endpoint['path']}`: {endpoint['purpose']}\n"
                    markdown_content += f"\n**Build In-House:** {'Yes' if spec['build_in_house'] else 'No'}\n"
                    markdown_content += f"**Reason:** {spec['reason']}\n\n"
            
            return markdown_content
        else:
            return f"Error: {response.text}"
    except Exception as e:
        return f"Error generating masterplan: {str(e)}"

def update_chat_history(history, message, is_user=True):
    """Update the chat history with new messages"""
    history = history or []
    return history + [[message, None] if is_user else [None, message]]

def clear_chat():
    """Clear the chat history"""
    return None

# Define the Gradio interface
with gr.Blocks(title="ChatGenesis - API Masterplan Generator") as demo:
    gr.Markdown("# ChatGenesis - API Masterplan Generator")
    gr.Markdown("Transform your business mission statement into a complete API specification masterplan.")
    
    with gr.Row():
        with gr.Column(scale=1):
            # Initial input form
            with gr.Group() as input_group:
                gr.Markdown("## Business Information")
                mission_input = gr.TextArea(label="Mission Statement / Operating Model", 
                                            placeholder="Enter your business mission statement or operating model...")
                company_name = gr.Textbox(label="Company Name (Optional)")
                industry = gr.Textbox(label="Industry (Optional)")
                business_size = gr.Dropdown(
                    label="Business Size (Optional)", 
                    choices=["Startup", "Small Business", "Medium Business", "Enterprise"]
                )
                
                ask_btn = gr.Button("Ask Follow-up Questions")
            
            # Questions and answers section  
            with gr.Group(visible=False) as questions_group:
                gr.Markdown("## Follow-up Questions")
                questions_box = gr.TextArea(label="Questions to Answer", interactive=False)
                answers_box = gr.TextArea(label="Your Answers", placeholder="Provide answers to the questions above...")
                generate_btn = gr.Button("Generate Masterplan")
            
        with gr.Column(scale=1):
            # Output section
            with gr.Group():
                gr.Markdown("## Masterplan Output")
                output = gr.Markdown()
            
            # Restart button
            restart_btn = gr.Button("Start New Masterplan")
    
    # Event handlers
    ask_btn.click(
        fn=lambda m, c, i, b: (
            gr.update(visible=True),
            "\n".join([f"{idx+1}. {q}" for idx, q in enumerate(ask_questions(m, c, i, b))])
        ),
        inputs=[mission_input, company_name, industry, business_size],
        outputs=[questions_group, questions_box]
    )
    
    generate_btn.click(
        fn=generate_masterplan,
        inputs=[mission_input, company_name, industry, business_size, answers_box],
        outputs=output
    )
    
    restart_btn.click(
        fn=lambda: (
            "", "", "", None, gr.update(visible=False), "", "", ""
        ),
        inputs=[],
        outputs=[mission_input, company_name, industry, business_size, 
                 questions_group, questions_box, answers_box, output]
    )

if __name__ == "__main__":
    demo.launch(share=False) 