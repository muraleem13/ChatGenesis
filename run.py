import argparse
import multiprocessing
import uvicorn
import gradio as gr
import app
from gradio_app import demo

def run_fastapi():
    """Run the FastAPI server"""
    uvicorn.run(app.app, host="0.0.0.0", port=8000)

def run_gradio():
    """Run the Gradio interface"""
    demo.launch(server_name="0.0.0.0", server_port=7860)

def run_both():
    """Run both the FastAPI server and Gradio interface in parallel"""
    fastapi_process = multiprocessing.Process(target=run_fastapi)
    gradio_process = multiprocessing.Process(target=run_gradio)
    
    fastapi_process.start()
    gradio_process.start()
    
    print("======================================")
    print("ChatOPT is running!")
    print("FastAPI server: http://localhost:8000")
    print("Gradio UI: http://localhost:7860")
    print("======================================")
    print("Press Ctrl+C to stop all services")
    
    try:
        fastapi_process.join()
        gradio_process.join()
    except KeyboardInterrupt:
        print("Shutting down...")
        fastapi_process.terminate()
        gradio_process.terminate()
        fastapi_process.join()
        gradio_process.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ChatOPT services")
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["fastapi", "gradio", "both"], 
        default="both",
        help="Which service to run (fastapi, gradio, or both)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "fastapi":
        print("Starting FastAPI server on http://localhost:8000")
        run_fastapi()
    elif args.mode == "gradio":
        print("Starting Gradio UI on http://localhost:7860")
        run_gradio()
    else:
        run_both() 