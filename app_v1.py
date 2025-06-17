import streamlit as st
import requests
import json
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import os
import numpy as np
from moviepy import ImageSequenceClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip

# Constants
API_KEY = "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"
VOICE_PATH = "output/voiceover.mp3"
VIDEO_PATH = "output/final_video.mp4"
FONT_PATH = "fonts/DejaVuSans.ttf"

def create_slide_image(text, slide_type="normal", width=1280, height=720):
    """Create slides with different styles"""
    try:
        # Set background and text colors based on slide type
        if slide_type == "title":
            bg_color = (240, 185, 46)  # Dark blue
            title_color = (255, 255, 255)
            body_color = (200, 200, 255)
        elif slide_type == "closing":
            bg_color = (61, 168, 113)  # Dark red
            title_color = (255, 255, 255)
            body_color = (255, 200, 200)
        else:
            bg_color = (104, 123, 217)  # Dark gray
            title_color = (255, 200, 100)
            body_color = (255, 255, 255)
        
        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype(FONT_PATH, 80 if slide_type in ["title", "closing"] else 60)
            body_font = ImageFont.truetype(FONT_PATH, 40)
        except:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
        
        # For title/ending slides
        if slide_type in ["title", "closing"]:
            title_bbox = draw.textbbox((0, 0), text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            draw.text(((width - title_width) // 2, height//2 - 50), text, 
                     font=title_font, fill=title_color)
            return img
        
        # For bullet point slides
        def wrap_text(text, font, max_width):
            lines = []
            for line in text.split("\n"):
                words = line.split()
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    test_bbox = draw.textbbox((0, 0), test_line, font=font)
                    test_width = test_bbox[2] - test_bbox[0]
                    
                    if test_width > max_width and current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        current_line.append(word)
                
                if current_line:
                    lines.append(' '.join(current_line))
            return lines
        
        # Process bullet points
        bullet_points = [bp.strip() for bp in text.split("\n") if bp.strip()]
        wrapped_lines = []
        
        for point in bullet_points:
            wrapped = wrap_text(point, body_font, width - 150)
            wrapped_lines.append(wrapped)
        
        # Draw bullet points
        y_position = 150
        bullet_gap = 60
        
        for i, point_lines in enumerate(wrapped_lines):
            # Draw bullet (•)
            draw.text((100, y_position + 5), "•", font=body_font, fill=body_color)
            
            # Draw text
            for j, line in enumerate(point_lines):
                draw.text((150, y_position + j*bullet_gap), line, font=body_font, fill=body_color)
            
            y_position += len(point_lines) * bullet_gap + 20
        
        return img
    except Exception as e:
        st.error(f"Error creating slide: {e}")
        return None

def generate_slides(product_name, script, voice_path=VOICE_PATH, output_path=VIDEO_PATH):
    """Generate professional slideshow video"""
    try:
        # Create title and ending slides
        title_slide = create_slide_image(product_name, "title")
        ending_slide = create_slide_image(product_name, "closing")

        #Removing first and last lines from script
        script_lines = [line.strip() for line in script.split("\n") if line.strip()]
        if len(script_lines) > 2:  # Only remove if we have enough content
            content_lines = script_lines[1:-1]  # Remove first and last line
        else:
            content_lines = script_lines


        # Create content slides (bullet points)
        content_slides = []
        for line in content_lines:
            slide = create_slide_image(line)
            if slide:
                content_slides.append(slide)
        
        if not content_slides:
            st.error("No valid content slides were created.")
            return None
        
        # Calculate durations
        if os.path.exists(voice_path):
            audio_clip = AudioFileClip(voice_path)
            total_duration = audio_clip.duration
            # Allocate time: 9s title, 9s ending, rest for content
            content_duration = (total_duration - 18) / len(content_slides)
        else:
            # Fallback timing
            content_duration = 4.0
        
        # Create video clips
        fps = 24
        clips = []
        
        # Title slide (9 seconds)
        clips.append(ImageSequenceClip([np.array(title_slide)] * int(9 * fps), fps=fps))
        
        # Content slides (dynamic duration)
        for slide in content_slides:
            frames = [np.array(slide)] * int(content_duration * fps)
            clips.append(ImageSequenceClip(frames, fps=fps))
        
        # Ending slide (9 seconds)
        clips.append(ImageSequenceClip([np.array(ending_slide)] * int(9 * fps), fps=fps))
        
        # Concatenate all clips
        final_video = concatenate_videoclips(clips)
        
        # Add audio if available
        if os.path.exists(voice_path):
            final_audio = CompositeAudioClip([audio_clip])
            final_video.audio = final_audio
        
        # Write video file
        final_video.write_videofile(
            output_path, 
            fps=fps, 
            codec='libx264', 
            audio_codec='aac',
            threads=4,
            preset='fast',
            ffmpeg_params=['-crf', '20']  # Better quality
        )

        return output_path
    except Exception as e:
        st.error(f"Error generating video: {e}")
        return str(e)

# Streamlit UI
st.title("🎬 Professional Video Slideshow Creator")
st.markdown("Create beautiful marketing videos automatically")

with st.form("video_form"):
    product_name = st.text_input("Product Name")
    audience = st.text_input("Target Audience")
    benefit = st.text_input("Key Benefit")
    tone = st.selectbox("Tone", ["Professional", "Friendly", "Persuasive"])
    
    submitted = st.form_submit_button("Generate Video")
    
    if submitted:
        if not all([product_name.strip(), audience.strip(), benefit.strip()]):
            st.warning("Please fill in both product name and key features")
        else:
            with st.spinner("Creating your professional video..."):
                try:
                    # Generate script with bullet points
                    prompt = f"""Create a video script for {product_name} targeting {audience}, 
                    highlighting {benefit} in a {tone.lower()} tone. Structure it as follows:
                    
                    1. Attention-Grabbing Opening
                    2. Problem Statement
                    3. Solution Overview
                    4. Key Benefits
                    
                    Make each section 2-3 sentences maximum. Separate sections with blank lines. 
                    start with {product_name} and end with strong call to action in one line and that line should last for 9sec.
                    give it in butten points and remove headers and bullet point symbol."""
                    
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
                    message = response.json()["choices"][0]["message"]["content"]
                    
                    st.success("Script generated successfully!")
                    with st.expander("View Script"):
                        st.text(message)
                    
                    # Generate voiceover
                    with st.spinner("Generating professional voiceover..."):
                        tts = gTTS(text=message, lang='en', slow=False)
                        tts.save(VOICE_PATH)
                        st.audio(VOICE_PATH)
                    
                    # Generate video
                    with st.spinner("Producing video slideshow..."):
                        final_path = generate_slides(product_name, message)
                        
                        if final_path and os.path.exists(final_path):
                            st.success("🎥 Video created successfully!")
                            st.video(final_path)
                        else:
                            st.error(f"Video creation failed: {final_path}")
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")