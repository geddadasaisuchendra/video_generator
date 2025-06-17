'''from mcp.server.fastmcp import FastMCP
# Create MCP server
mcp = FastMCP("VideoGenerator")



# --- Child Tool 1: Script Generator ---
@mcp.tool()
def generate_script(
    product_name: str,
    audience: str,
    benefit: str,
    description: str = "",
    tone: str = "Professional"
) -> str:
    """Generate formatted video script using Claude's capabilities."""
    return f"""
    ### Product Info
    Name: {product_name}
    Audience: {audience}
    Benefit: {benefit}
    Description: {description}
    Tone: {tone}
    
    ### Audio Script
    Introducing {product_name}, the perfect solution for {audience} who need {benefit}.
    With its {description}, this innovative product delivers outstanding results.
    Experience the difference today with {product_name} - your solution for {benefit}.
    Don't wait - try {product_name} now!
    
    ### Visual Prompts
    1. A {product_name} being used by {audience}, showing {benefit} in action
    2. Close-up of {product_name} highlighting {description}
    3. {audience} smiling while using {product_name} in real-world scenario
    4. {product_name} packaging with call-to-action message
    """

# --- Child Tool 2: Video Creator ---

@mcp.tool()
def create_video(script: str) -> str:
    """Generate video from formatted script."""
    try:
        #imports
        import os   # for file manipulation
        import requests  # api call
        import json      # api call
        import base64    # image
        from gtts.tts import gTTS # audio generation
        from moviepy import ImageClip, AudioFileClip, concatenate_videoclips,CompositeAudioClip  # video generation
        from PIL import Image #image
        from io import BytesIO # image

        # Configuration
        PROJECTS_DIR = "video_generator"
        VOICE_PATH = "output/voiceover.mp3"
        APIFY_TOKEN = "apify_api_YJ0aGFeLj9iCc8s7EWHCDwaiwgYXRl1ZCWLJ"
        ACTOR_TASK_ID = "g.saisuchendra~text-to-image-generator-task"
        
        # Extract product name for folder
        product_name = "product"
        if "Name: " in script:
            product_name = script.split("Name: ")[1].split("\n")[0].strip()
        
        # Split script sections
        audio_part = script.split("### Audio Script")[1].split("### Visual Prompts")[0].strip()
        visual_part = script.split("### Visual Prompts")[1].strip()
        visual_prompts = [line.strip() for line in visual_part.split("\n") if line.strip() and line[0].isdigit()]

        # Generate voiceover
        tts = gTTS(text=audio_part, lang='en', slow=False)
        tts.save(VOICE_PATH)

        # Generate images
        project_folder = os.path.join(PROJECTS_DIR, product_name)
        images_folder = os.path.join(project_folder, "images")
        os.makedirs(images_folder, exist_ok=True)
        image_paths = []
        
        for i, image_prompt in enumerate(visual_prompts):
            payload = {
                "prompt": image_prompt.split(". ")[1],  # Remove numbering
                "width": 1024,
                "height": 768
            }
            url = f"https://api.apify.com/v2/actor-tasks/{ACTOR_TASK_ID}/run-sync-get-dataset-items?token={APIFY_TOKEN}"
            res = requests.post(url, json=payload)
            if 'image' in res.json()[0]:
                base64_data = res.json()[0]['image'].split(",")[1]
                img_data = BytesIO(base64.b64decode(base64_data))
                img = Image.open(img_data)
                path = os.path.join(images_folder, f"scene_{i+1}.jpg")
                img.save(path)
                image_paths.append(path)

        # Generate video
        audio = AudioFileClip(VOICE_PATH)
        audio_duration = audio.duration
        per_image_duration = audio_duration / len(image_paths)

        clips = []
        for img_path in image_paths:
            img_clip = ImageClip(img_path).with_duration(per_image_duration)
            clips.append(img_clip)

        final_video = concatenate_videoclips(clips, method="compose")
        final_video = final_video.with_audio(CompositeAudioClip([audio]))

        output_path = os.path.join(project_folder, "final_video.mp4")
        final_video.write_videofile(output_path, fps=24)

        return f"Video successfully generated at: {output_path}"

    except Exception as e:
        return f"Error creating video: {str(e)}"

# --- Parent Tool ---
@mcp.tool()
def generate_marketing_video(
    product_name: str,
    audience: str,
    benefit: str,
    description: str = "",
    tone: str = "Professional"
) -> str:
    """Complete video generation workflow (calls child tools internally)."""
    try:
       
        # Step 1: Generate script
        script = generate_script(
            product_name=product_name,
            audience=audience,
            benefit=benefit,
            description=description,
            tone=tone
        )
        
        # Step 2: Create video
        result = create_video(script=script)
        
        return result
        
    except Exception as e:
        return f"Error in video generation pipeline: {str(e)}"

# --- Help Resource ---
@mcp.resource("videogen://help")
def get_help() -> str:
    """Get usage instructions"""
    return """Video Generator Tools:
    
1. generate_marketing_video(
    product_name: str,
    audience: str,
    benefit: str,
    description: str = "",
    tone: str = "Professional"
) -> str
    
Example:
generate_marketing_video(
    product_name="Smart Bottle",
    audience="Athletes",
    benefit="Hydration Tracking",
    description="500ml with digital display",
    tone="Persuasive"
)
"""

if __name__ == "__main__":
    mcp.run()





'''


from mcp.server import Server
from mcp import types
import anyio
from anyio.streams.memory import MemoryObjectSendStream, MemoryObjectReceiveStream
from typing import Dict, List
import os
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
from PIL import Image
from io import BytesIO
import requests
import base64

# Initialize server
server = Server("VideoGenerator")

# Configuration
CONFIG = {
    "PROJECTS_DIR": "video_generator",
    "VOICE_PATH": "output/voiceover.mp3",
    "APIFY_TOKEN": "apify_api_YJ0aGFeLj9iCc8s7EWHCDwaiwgYXRl1ZCWLJ",
    "ACTOR_TASK_ID": "g.saisuchendra~text-to-image-generator-task"
}

# --- Stream Setup ---
async def setup_streams():
    send_stream, receive_stream = anyio.create_memory_object_stream(max_buffer_size=1000)
    return receive_stream, send_stream

# --- Tool Implementation ---
async def generate_script(params: Dict) -> List[types.TextContent]:
    script = f"""
    ### Product Info
    Name: {params['product_name']}
    Audience: {params['audience']}
    Benefit: {params['benefit']}
    
    ### Audio Script
    Introducing {params['product_name']}, the perfect solution for {params['audience']}...
    """
    return [types.TextContent(type="text", text=script)]

async def create_video(params: Dict) -> List[types.TextContent]:
    try:
        # Voiceover
        tts = gTTS(text=params['script'], lang='en')
        tts.save(CONFIG["VOICE_PATH"])
        
        # Images
        image_paths = []
        for i, prompt in enumerate(params['visual_prompts'][:4]):
            res = requests.post(
                f"https://api.apify.com/v2/actor-tasks/{CONFIG['ACTOR_TASK_ID']}/run-sync-get-dataset-items",
                json={"prompt": prompt, "width": 1024, "height": 768},
                headers={"Authorization": f"Bearer {CONFIG['APIFY_TOKEN']}"}
            )
            img_data = base64.b64decode(res.json()[0]['image'].split(",")[1])
            img_path = f"{CONFIG['PROJECTS_DIR']}/scene_{i}.jpg"
            Image.open(BytesIO(img_data)).save(img_path)
            image_paths.append(img_path)
        
        # Video
        audio = AudioFileClip(CONFIG["VOICE_PATH"])
        clips = [ImageClip(p).with_duration(audio.duration/len(image_paths)) for p in image_paths]
        output_path = f"{CONFIG['PROJECTS_DIR']}/{params['product_name']}.mp4"
        concatenate_videoclips(clips).with_audio(audio).write_videofile(output_path, fps=24)
        
        return [types.TextContent(type="text", text=f"Video created: {output_path}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}", isError=True)]

# --- Tool Registration ---
@server.list_tools()
async def list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="generate_script",
            description="Creates video scripts",
            parameters={
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "audience": {"type": "string"},
                    "benefit": {"type": "string"}
                },
                "required": ["product_name", "audience", "benefit"]
            }
        ),
        types.Tool(
            name="create_video",
            description="Renders marketing videos", 
            parameters={
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "script": {"type": "string"},
                    "visual_prompts": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["product_name", "script", "visual_prompts"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict) -> List[types.TextContent]:
    if name == "generate_script":
        return await generate_script(arguments)
    elif name == "create_video":
        return await create_video(arguments)
    return [types.TextContent(type="text", text="Unknown tool", isError=True)]

# --- Main Execution ---
async def main():
    # Create streams
    read_stream, write_stream = await setup_streams()
    
    # Prepare initialization options
    init_options = server.create_initialization_options()
    
    # Ensure output directory exists
    os.makedirs(CONFIG["PROJECTS_DIR"], exist_ok=True)
    
    # Run server
    await server.run(
        read_stream=read_stream,
        write_stream=write_stream,
        initialization_options=init_options
    )

if __name__ == "__main__":
    anyio.run(main)