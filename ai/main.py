import os
import json
import subprocess
import re
from fastapi import FastAPI, HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import cloudinary
from pydantic import BaseModel
import cloudinary.uploader
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

from utils import run_manim, generate_safe_filename, extract_code_script_and_mcq
# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)


async def upload_to_cloudinary(file_path, resource_type):
    try:
        result = cloudinary.uploader.upload(file_path, resource_type=resource_type)
        return result['secure_url']
    except Exception as e:
        print(f"Error uploading to Cloudinary: {str(e)}")
        raise


app = FastAPI()





app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


chate = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

class ChatInput(BaseModel):
    message: str

@app.post("/chat/")
async def chat_with_gpt(input: ChatInput):
    try:
        # Create a message with the user's input
        message = HumanMessage(content=input.message)

        # Get the response from the language model
        response = chate.invoke([message])

        # Return the response content
        return {"response": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Initialize the language model
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

MAX_RETRIES = 3

@app.post("/generate_video/")
async def generate_video(title: str):
    print("received request: ", title)
    safe_filename = generate_safe_filename(title)
    output_file = f"{safe_filename}.mp4"
    print("output_file: ", output_file)
    for attempt in range(MAX_RETRIES):
        print("attempt: ", attempt)
        try:
            messages = [
                ("system", "You are a helpful assistant that creates educational videos for kids."),
                ("human", f"""Generate Manim code for a short video on '{title}'. Please provide:
                1. Python code for Manim (name the class 'Video')
                2. A text script with timings for narration
                3. Five MCQ questions about the video content

                Format your response as follows:
                ```python
                [Manim Python code here]
                ```

                ```script
                0:00 - [Narration for the start of the video]
                0:05 - [Next line of narration]
                ...
                [Continue with timing and narration]
                ```

                ```mcq
                [
                    {{
                        "question": "[Question 1]",
                        "options": ["[Option 1]", "[Option 2]", "[Option 3]", "[Option 4]"],
                        "correctAnswer": "[Correct option for Question 1]"
                    }},
                    {{
                        "question": "[Question 2]",
                        "options": ["[Option 1]", "[Option 2]", "[Option 3]", "[Option 4]"],
                        "correctAnswer": "[Correct option for Question 2]"
                    }},
                    {{
                        "question": "[Question 3]",
                        "options": ["[Option 1]", "[Option 2]", "[Option 3]", "[Option 4]"],
                        "correctAnswer": "[Correct option for Question 3]"
                    }},
                    {{
                        "question": "[Question 4]",
                        "options": ["[Option 1]", "[Option 2]", "[Option 3]", "[Option 4]"],
                        "correctAnswer": "[Correct option for Question 4]"
                    }},
                    {{
                        "question": "[Question 5]",
                        "options": ["[Option 1]", "[Option 2]", "[Option 3]", "[Option 4]"],
                        "correctAnswer": "[Correct option for Question 5]"
                    }}
                ]
                ```
                """),
            ]

            # Call the Gemini LLM
            ai_response = llm.invoke(messages)

            if not ai_response.content:
                raise HTTPException(status_code=500, detail="Failed to generate code")
            print("ai_response.content: ", ai_response.content)
            # Extract the Python code using regular expressions
            python_code, parsed_script, mcq = extract_code_script_and_mcq(ai_response.content)
            print("script: ", mcq)
            if not python_code:
                raise ValueError("No Python code found in the API response.")

            
            # Write only the extracted Python code to the file
            with open('generate_manim.py', 'w') as f:
                f.write(python_code)
            print("python code written to file attempt: ", attempt)
            # Run the generated Manim file
            await run_manim(output_file)
            print(f"Attempt {attempt + 1}: Successfully ran the generated code")

            # Construct the path to the generated video
            generic_path = f"media/videos/generate_manim/480p15/{output_file}"
            mcq_file = f"mcq/{safe_filename}.json"
            with open(mcq_file, 'w') as f:
                json.dump(mcq, f, indent=2)
            
            # Check if the video file exists
            if not os.path.exists(generic_path):
                raise FileNotFoundError("Video file not created")
            video_url = await upload_to_cloudinary(generic_path, 'video')
            mcq_url = await upload_to_cloudinary(mcq_file, 'raw')
            os.remove(generic_path)
            os.remove(mcq_file)
            return {"video_url": video_url, "mcq_url": mcq_url}

        except Exception as e:
            error_message = str(e)
            print(f"Attempt {attempt + 1} failed: {error_message}")

            if attempt < MAX_RETRIES - 1:
                # Prepare for retry
                retry_messages = [
                    ("system", "You are a helpful assistant that creates video for kids for educational purposes."),
                    ("human", f"The previous attempt to generate Manim code for '{title}' failed with the error: {error_message}. Please provide an improved version of the code that addresses this issue. Remember to name the class as 'Video' for the scene."),
                    ("human", f"Here's the previously generated code for reference:\n\n{python_code}")
                ]
                messages = retry_messages
            else:
                # All attempts failed
                raise HTTPException(status_code=500, detail=f"Failed to generate video after {MAX_RETRIES} attempts. Last error: {error_message}")

    # This line should never be reached due to the loop structure, but including it for completeness
    raise HTTPException(status_code=500, detail="Unexpected error in video generation process")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
