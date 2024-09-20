import os
import json
import subprocess
import re
from fastapi import FastAPI, HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import cloudinary
from pydantic import BaseModel, Field
import cloudinary.uploader
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from typing import List, Tuple
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from typing import List

from utils import run_manim, generate_safe_filename, extract_code_script_and_mcq, generate_image, text_to_speech, save_image
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
    model_name="gpt-4-turbo",
    openai_api_key=OPENAI_API_KEY
)

class MCQ(BaseModel):
    question: str
    options: List[str]
    correctAnswer: str

class EducationalContent(BaseModel):
    scenes: List[Tuple[str, str]] = Field(description="List of tuples containing scene descriptions and narration scripts")
    mcqs: List[MCQ] = Field(description="List of 5 multiple-choice questions")
    short_topic: str = Field(description="A catchy title for the video")

class ContentRequest(BaseModel):
    topic: str
    grade: int

# Create a parser
parser = PydanticOutputParser(pydantic_object=EducationalContent)

# Create a prompt template
prompt_template = ChatPromptTemplate.from_template(
    """You are an AI system for generating educational content for students. 
    Create concise scene descriptions and corresponding narration scripts for some scenes tailored for a student of grade {grade}. 
    Additionally, provide 5 multiple-choice questions (MCQs) related to the topic and short catchy video title

    The topic is: {topic}

    {format_instructions}
    """
)


@app.post("/generate_educational_content/")
async def generate_educational_content(request: ContentRequest):
    try:
        # Step 1: Format the prompt with user's input and desired output format
        prompt = prompt_template.format_prompt(
            grade=request.grade,
            topic=request.topic,
            format_instructions=parser.get_format_instructions()
        )

        # Step 2: Get the response from the language model
        response = chate.invoke(prompt.to_messages())

        # Step 3: Parse the response
        parsed_response = parser.parse(response.content)

        # Step 4: Generate images using DALL-E for each scene description
        image_files = []
        for i, scene_description in enumerate(parsed_response.scenes):
            files = generate_image(scene_description[0], i)  # Call DALL-E or similar
            image_files.extend(files)

        # Step 5: Convert narration scripts to audio using a Text-to-Speech engine
        audio_files = []
        caption = ""
        for i, narration_script in enumerate(parsed_response.scenes):
            filename = f"temp_audio_{i}.mp3"
            text_to_speech(narration_script[1], filename)  # Convert narration to speech
            audio_files.append(filename)
            caption += narration_script[1]

        # Step 6: Assemble the video using MoviePy
        def assemble_video(scene_images: List[str], audio_files: List[str], output_filename: str = "educational_video.mp4"):
            clips = []
            for audio_index, audio_file in enumerate(audio_files):
                audio_clip = AudioFileClip(audio_file)
                image_duration = audio_clip.duration / len(scene_images[audio_index * 5:(audio_index + 1) * 5])
                
                for img_index in range(audio_index * 5, (audio_index + 1) * 5):
                    image_clip = ImageClip(scene_images[img_index]).set_duration(image_duration)
                    start_time = (img_index % 5) * image_duration
                    image_clip = image_clip.set_audio(audio_clip.subclip(start_time, start_time + image_duration))
                    clips.append(image_clip)
                    
            final_video = concatenate_videoclips(clips, method="compose")
            final_video.write_videofile(output_filename, fps=1)

        # Call the video assembly function
        video_filename = "educational_video.mp4"
        assemble_video(image_files, audio_files, video_filename)

        

        upload_result = cloudinary.uploader.upload_large(video_filename, resource_type="video")
        video_url = upload_result['secure_url']

        # Step 8: Upload thumbnail (using first image as thumbnail)
        thumbnail = cloudinary.uploader.upload(image_files[0])

        # Clean up temp files (optional)
        for file in image_files + audio_files:
            os.remove(file)
        os.remove(video_filename)

        # Step 9: Return the result, including the video link, thumbnail, and MCQs
        return {
            "video_title": parsed_response.short_topic,
            "caption": caption,
            "description": request.topic,
            "thumbnail": thumbnail["secure_url"],
            "video_link": video_url,
            "mcqs": parsed_response.mcqs
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




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
