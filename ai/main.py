import os
import json
import subprocess
import re
from fastapi import FastAPI, HTTPException
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

from utils import run_manim, generate_safe_filename, generate_image, text_to_speech, save_image, add_audio_to_video
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
    description:str = Field(description="short description summarizing the content of video")

class ContentRequest(BaseModel):
    topic: str
    grade: int




@app.post("/generate_educational_content/")
async def generate_educational_content(request: ContentRequest):
    prompt_template = ChatPromptTemplate.from_template(
        """You are an AI system for generating educational video content for students. 
        Additionally, provide 5 multiple-choice questions (MCQs) related to the topic and short catchy video title and desc

        The topic is: {topic}

        {format_instructions}
        If the topic in not related to the education, leave each field empty.
        """
    )
    parser = PydanticOutputParser(pydantic_object=EducationalContent)


    try:
        # Step 1: Format the prompt with user's input and desired output format
        prompt = prompt_template.format_prompt(
            grade=request.grade,
            topic=request.topic,
            format_instructions=parser.get_format_instructions()
        )

        # Step 2: Get the response from the language model
        response = chate.invoke(prompt.to_messages())
        print("chate response ", response)
        # Step 3: Parse the response
        parsed_response = parser.parse(response.content)
        if not parsed_response.scenes:
            raise HTTPException(status_code=400, detail="The title field is empty. Please provide a relevant topic.")
            
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


class MathContent(BaseModel):
    manim_code: str = Field(description="manim script in python to generate the video according to the user's query. make the video at least 20 seconds long or more")
    caption:str = Field(description="Narration script to narrate the texts in video and the video itself in one sentence")
    mcqs: List[MCQ] = Field(description="List of 5 multiple-choice questions")
    short_topic: str = Field(description="A catchy title for the video")
    description:str = Field(description="short description summarizing the content of video")
    # thumbnail:str = Field(description="link to an image that can act like thubnail for this video")



MAX_RETRIES = 3



@app.post("/generate_math_video/")
async def generate_math_video(request: ContentRequest):
    print("received request: ", request.topic)
    safe_filename = generate_safe_filename(request.topic)
    output_file = f"{safe_filename}.mp4"
    print("output_file: ", output_file)
    
    message = f"""You are an AI system for generating educational mathematics video content for students of grade {request.grade}. 
            you can add more details relevant to the topic. then generate the manim code for the video. make the visualization colorful. add on screen texts. text must not cover the main contain.
                Additionally, provide 5 multiple-choice questions (MCQs) related to the topic and short catchy video title and desc

                The topic is: {request.topic}

                {{format_instructions}}
                If the topic is not related to education, leave each field empty.
                """
    
    parser = PydanticOutputParser(pydantic_object=MathContent)
    prompt_template = ChatPromptTemplate.from_template(message)
    
    for attempt in range(MAX_RETRIES):
        print("attempt: ", attempt)
        try:
            prompt = prompt_template.format_prompt(
                grade=request.grade,
                topic=request.topic,
                format_instructions=parser.get_format_instructions()
            )
            response = await chate.ainvoke(prompt.to_messages())
            parsed_response = parser.parse(response.content)
            
            if not parsed_response.manim_code:
                raise ValueError("No Python code found in the API response.")

            # Write only the extracted Python code to the file
            with open('manim_code.py', 'w') as f:
                f.write(parsed_response.manim_code)
            print("python code written to file attempt: ", attempt)
            
            # Run the generated Manim file
            await run_manim(output_file)
            print(f"Attempt {attempt + 1}: Successfully ran the generated code")

            # Construct the path to the generated video
            generic_path = f"media/videos/manim_code/480p15/{output_file}"
            text_to_speech(parsed_response.caption, "temp_math_audio.mp3")
            add_audio_to_video(generic_path, "temp_math_audio.mp3", generic_path)
            # Check if the video file exists
            if not os.path.exists(generic_path):
                raise FileNotFoundError("Video file not created")
            
            
            video_url = await upload_to_cloudinary(generic_path, 'video')
            
            # # Clean up files
            for file_path in [generic_path, "manim_code.py", "temp_math_audio.mp3"]:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            return {
                "video_title": parsed_response.short_topic,
                "caption": parsed_response.caption,
                "description": parsed_response.caption,
                "thumbnail": "",
                "video_link": video_url,
                "mcqs": parsed_response.mcqs
            }
            
        except Exception as e:
            error_message = str(e)
            print(f"Attempt {attempt + 1} failed: {error_message}")

            if attempt < MAX_RETRIES - 1:
                # Prepare for retry
                retry_message = f"""You are a helpful assistant that creates video for kids for educational purposes.
                    The previous attempt to generate Manim code for '{request.topic}' failed with the error: {error_message}. 
                    Please provide an improved version of the code that addresses this issue. 
                    Remember to name the class as 'Video' for the scene.
                    Here's the previously generated code for reference:\n\n{parsed_response.manim_code}"""
                
                message = retry_message
            else:
                # All attempts failed
                raise HTTPException(status_code=500, detail=f"Failed to generate video after {MAX_RETRIES} attempts. Last error: {error_message}")

    # This line should never be reached due to the loop structure, but including it for completeness
    raise HTTPException(status_code=500, detail="Unexpected error in video generation process")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)