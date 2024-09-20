import asyncio
import os
import re
import time
import json

async def run_manim(output_file):
    try:
        # Run the manim command with the specified output file
        os.system(f'manim generate_manim.py Video -ql -o {output_file}')
        print("Manim execution completed successfully")
    except Exception as e:
        print(f"Error running Manim: {str(e)}")
        raise



def generate_safe_filename(title):
    # Remove or replace characters that are unsafe for filenames
    safe_title = re.sub(r'[^\w\-_\. ]', '', title)
    safe_title = safe_title.replace(' ', '_').lower()
    timestamp = int(time.time())
    return f"{safe_title}_{timestamp}"




# def extract_code_and_script(content):
#     code_pattern = re.compile(r'```python\n(.*?)```', re.DOTALL)
#     code_match = code_pattern.search(content)
    
#     script_pattern = re.compile(r'```script\n(.*?)```', re.DOTALL)
#     script_match = script_pattern.search(content)
    
#     if not code_match or not script_match:
#         raise ValueError("Could not extract both code and script from the response.")
    
#     python_code = code_match.group(1)
#     raw_script = script_match.group(1)
    
#     # Parse the raw script into a list of tuples
#     script_lines = raw_script.strip().split('\n')
#     parsed_script = []
    
#     for line in script_lines:
#         # Match time and text
#         match = re.match(r'(\d+:\d+)\s*-\s*(.*)', line.strip())
#         if match:
#             time_str, text = match.groups()
#             # Convert time to seconds
#             minutes, seconds = map(int, time_str.split(':'))
#             time_seconds = minutes * 60 + seconds
#             parsed_script.append((time_seconds, text.strip()))
    
#     return python_code, parsed_script


def extract_code_script_and_mcq(content):
    code_pattern = re.compile(r'```python\n(.*?)```', re.DOTALL)
    script_pattern = re.compile(r'```script\n(.*?)```', re.DOTALL)
    mcq_pattern = re.compile(r'```mcq\n(.*?)```', re.DOTALL)
    
    code_match = code_pattern.search(content)
    script_match = script_pattern.search(content)
    mcq_match = mcq_pattern.search(content)
    
    if not code_match or not script_match or not mcq_match:
        raise ValueError("Could not extract code, script, and MCQ from the response.")
    
    python_code = code_match.group(1)
    raw_script = script_match.group(1)
    mcq_json = mcq_match.group(1)
    
    # Parse the raw script into a list of tuples
    script_lines = raw_script.strip().split('\n')
    parsed_script = []
    
    for line in script_lines:
        match = re.match(r'(\d+:\d+)\s*-\s*(.*)', line.strip())
        if match:
            time_str, text = match.groups()
            minutes, seconds = map(int, time_str.split(':'))
            time_seconds = minutes * 60 + seconds
            parsed_script.append((time_seconds, text.strip()))
    
    # Parse the MCQ JSON
    mcq = json.loads(mcq_json)
    
    return python_code, parsed_script, mcq



if __name__ == "__main__":
    asyncio.run(run_manim("test1"))
    # content = """
    # ```python
    # from manim import *
    
    # class Video(Scene):
    #     def construct(self):
    #         # Manim code here
    # ```
    
    # ```script
    # 0:00 - Welcome to our video about triangles!
    # 0:05 - A triangle is a shape with three sides and three angles.
    # 1:10 - Let's draw a triangle and explore its properties.
    # ```
    # """
    
    # code, script = extract_code_and_script(content)
    # print("Python Code:")
    # print(code)
    # print("\nParsed Script:", script)
    # for time, text in script:
    #     print(f"{time} seconds: {text}")