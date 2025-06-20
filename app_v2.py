'''
#For local purpose

import os   # for file manipulation
import requests  # api call
import json      # api call
import base64    # image
from gtts import gTTS # audio generation
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips,CompositeAudioClip  # video generation
from PIL import Image #image
from io import BytesIO # image
import streamlit as st # for ui

# === PATH CONFIG ===
PROJECTS_DIR = "video_generator"
VOICE_PATH = "output/voiceover.mp3"
API_KEY = st.secrets["openrouter"]["API_KEY"]
APIFY_TOKEN = st.secrets["apify"]["APIFY_TOKEN"]
ACTOR_TASK_ID = st.secrets["apify"]["ACTOR_TASK_ID"]


# === Streamlit UI ===
st.title("\U0001F3AC Ai Sales Video Generator")
st.markdown("Create beautiful marketing videos automatically...")

with st.form("video_form"):
    product_name = st.text_input("Product Name")
    audience = st.text_input("Target Audience")
    benefit = st.text_input("Key Benefit")
    description = st.text_input("Description",placeholder="provide related desc  (like color, shape, size, ...etc)")
    tone = st.selectbox("Tone", ["Professional", "Friendly", "Persuasive"])

    submitted = st.form_submit_button("Generate Video")

    if submitted:
        if not all([product_name.strip(), audience.strip(), benefit.strip()]):
            st.warning("Please fill in all fields")
        else:
            with st.spinner("Creating your professional video..."):
                try:
                    # === Step 1: Generate script ===
                    prompt = f"""
                            Create a video plan for the product **{product_name}**, targeting **{audience}**, highlighting **{benefit}**, description **{description}, and using a **{tone.lower()}** tone.

                            Give your response in this format:

                            ### Audio Script
                            Write 4 short scenes (each 2–3 sentences) meant to be spoken in a voiceover.Remove Headers for Each Sentence. Make sure it starts with {product_name} and ends with a call to action.

                            ### Visual Prompts
                            For each of the 4 scenes, write a matching detailed image generation prompt (for AI tools) that describes what to show visually — e.g. UI mockups, people, devices, emotions, etc.scene description is not needed just image prompt is enough.
                        """

                    headers = {
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json",
                    }
                    payload = {
                        "model": "meta-llama/llama-3.3-8b-instruct:free",
                        "messages": [{"role": "user", "content": prompt}]
                    }

                    response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        data=json.dumps(payload),
                        timeout=30
                    )
                    print(response.json())
                    message = response.json()["choices"][0]["message"]["content"]
                    audio_part =""
                    visual_part=""

                    if "### Audio Script" in message and "### Visual Prompts" in message:
                        parts = message.split("### Visual Prompts")
                        audio_part = parts[0].replace("### Audio Script","").strip()
                        visual_part = parts[1].strip()

                    st.success("Script generated successfully!")
                    with st.expander("View Script"):
                        st.text(message)

                    # === Step 2: Generate voiceover ===
                    tts = gTTS(text=audio_part, lang='en', slow=False)
                    tts.save(VOICE_PATH)
                    st.audio(VOICE_PATH)

                    # === Step 3: Generate scene-level visual prompts ===
                    scene_lines = [s.strip() for s in message.split("\n") if s.strip()]
                    visual_prompts = [line.strip() for line in visual_part.split("\n") if line.strip()]
                    st.write(visual_prompts)

                    # === Step 4: Generate images ===
                    project_folder = os.path.join(PROJECTS_DIR, product_name)
                    images_folder = os.path.join(project_folder, "images")
                    os.makedirs(images_folder, exist_ok=True)
                    image_paths = []

                    for i, image_prompt in enumerate(visual_prompts):
                        payload = {
                            "prompt": image_prompt,
                            "width": 1024,
                            "height": 768
                        }
                        url = f"https://api.apify.com/v2/actor-tasks/{ACTOR_TASK_ID}/run-sync-get-dataset-items?token={APIFY_TOKEN}"
                        res = requests.post(url, json=payload)
                        st.write(res.json())
                        if 'image' in res.json()[0]:
                            base64_data = res.json()[0]['image'].split(",")[1]
                            img_data = BytesIO(base64.b64decode(base64_data))
                            img = Image.open(img_data)
                            path = os.path.join(images_folder, f"scene_{i+1}.jpg")
                            img.save(path)
                            image_paths.append(path)

                    # === Step 5: Generate video ===
                    audio = AudioFileClip(VOICE_PATH)
                    audio_duration = audio.duration
                    per_image_duration = audio_duration / len(image_paths)

                    clips = []
                    for img_path in image_paths:
                        img_clip = ImageClip(img_path).with_duration(per_image_duration).resized(lambda t: 1 + 0.05 * t)
                        clips.append(img_clip)

                    final_video = concatenate_videoclips(clips, method="compose")
                    final_video = final_video.with_audio(CompositeAudioClip([audio]))

                    output_path = os.path.join(project_folder, "final_video.mp4")
                    final_video.write_videofile(output_path, fps=24)

                    st.success("\U0001F3A5 Video created successfully!")
                    st.video(output_path)

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
'''


#for deployement
import os
import requests
import json
import base64
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
from PIL import Image
from io import BytesIO
import streamlit as st
import tempfile

# === Streamlit UI ===
st.title("\U0001F3AC Ai Sales Video Generator")
st.markdown("Create beautiful marketing videos automatically...")

with st.form("video_form"):
    product_name = st.text_input("Product Name")
    audience = st.text_input("Target Audience")
    benefit = st.text_input("Key Benefit")
    description = st.text_input("Description", placeholder="provide related desc (like color, shape, size, ...etc)")
    tone = st.selectbox("Tone", ["Professional", "Friendly", "Persuasive"])

    submitted = st.form_submit_button("Generate Video")

    if submitted:
        if not all([product_name.strip(), audience.strip(), benefit.strip()]):
            st.warning("Please fill in all fields")
        else:
            with st.spinner("Creating your professional video..."):
                try:
                    # === Step 1: Generate script ===
                    prompt = f"""
                        Create a video plan for the product **{product_name}**, targeting **{audience}**, highlighting **{benefit}**, description **{description}, and using a **{tone.lower()}** tone.

                        Give your response in this format:

                        ### Audio Script
                        Write 4 short scenes (each 2–3 sentences) meant to be spoken in a voiceover.Remove Headers for Each Sentence. Make sure it starts with {product_name} and ends with a call to action.

                        ### Visual Prompts
                        For each of the 4 scenes, write a matching detailed image generation prompt (for AI tools) that describes what to show visually — e.g. UI mockups, people, devices, emotions, etc.scene description is not needed just image prompt is enough.
                    """

                    headers = {
                        "Authorization": f"Bearer {st.secrets['openrouter']['API_KEY']}",
                        "Content-Type": "application/json",
                    }
                    payload = {
                        "model": "meta-llama/llama-3.3-8b-instruct:free",
                        "messages": [{"role": "user", "content": prompt}]
                    }

                    response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        data=json.dumps(payload),
                        timeout=30
                    )
                    message = response.json()["choices"][0]["message"]["content"]
                    audio_part = ""
                    visual_part = ""

                    if "### Audio Script" in message and "### Visual Prompts" in message:
                        parts = message.split("### Visual Prompts")
                        audio_part = parts[0].replace("### Audio Script", "").strip()
                        visual_part = parts[1].strip()

                    st.success("Script generated successfully!")
                    with st.expander("View Script"):
                        st.text(message)

                    # === Step 2: Generate voiceover ===
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as voice_temp:
                        tts = gTTS(text=audio_part, lang='en', slow=False)
                        tts.save(voice_temp.name)
                        st.audio(voice_temp.name)
                        voice_path = voice_temp.name

                    # === Step 3: Generate scene-level visual prompts ===
                    visual_prompts = [line.strip() for line in visual_part.split("\n") if line.strip()]
                    
                    # === Step 4: Generate images ===
                    with tempfile.TemporaryDirectory() as temp_dir:
                        image_paths = []
                        
                        for i, image_prompt in enumerate(visual_prompts):
                            payload = {
                                "prompt": image_prompt,
                                "width": 1024,
                                "height": 768
                            }
                            url = f"https://api.apify.com/v2/actor-tasks/{st.secrets['apify']['ACTOR_TASK_ID']}/run-sync-get-dataset-items?token={st.secrets['apify']['APIFY_TOKEN']}"
                            res = requests.post(url, json=payload)
                            print(res)
                            if 'image' in res.json()[0]:
                                base64_data = res.json()[0]['image'].split(",")[1]
                                img_data = BytesIO(base64.b64decode(base64_data))
                                img = Image.open(img_data)
                                path = os.path.join(temp_dir, f"scene_{i+1}.jpg")
                                img.save(path)
                                image_paths.append(path)

                        # === Step 5: Generate video ===
                        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_temp:
                            try:
                                audio = AudioFileClip(voice_path)
                                audio_duration = audio.duration
                                per_image_duration = audio_duration / len(image_paths) if image_paths else 1

                                clips = []
                                for img_path in image_paths:
                                    img_clip = ImageClip(img_path).with_duration(per_image_duration)
                                    clips.append(img_clip)

                                final_video = concatenate_videoclips(clips, method="compose")
                                final_video = final_video.with_audio(CompositeAudioClip([audio]))
                                final_video.write_videofile(video_temp.name, fps=24, codec='libx264', audio_codec='aac')
                                
                                # Display the video
                                st.success("\U0001F3A5 Video created successfully!")
                                video_bytes = open(video_temp.name, "rb").read()
                                st.video(video_bytes)
                                
                            finally:
                                # Clean up resources
                                if 'audio' in locals():
                                    audio.close()
                                if 'final_video' in locals():
                                    final_video.close()
                                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    if 'voice_path' in locals() and os.path.exists(voice_path):
                        os.unlink(voice_path)
                    if 'video_temp' in locals() and os.path.exists(video_temp.name):
                        os.unlink(video_temp.name)