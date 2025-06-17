'''"""import requests
import base64
from PIL import Image
from io import BytesIO

API_TOKEN = "apify_api_YJ0aGFeLj9iCc8s7EWHCDwaiwgYXRl1ZCWLJ"

url = "https://api.apify.com/v2/actor-tasks/g.saisuchendra~text-to-image-generator-task/run-sync-get-dataset-items?token=" + API_TOKEN

payload = {
    "prompt": "Professional product photo of a time tracking app, clean background, minimal UI, 3D look",
    "width": 1024,
    "height": 768
}

response = requests.post(url, json=payload)
#print(response.json())


result = response.json()
if isinstance(result, list) and 'image' in result[0]:
    data_uri = result[0]['image']
    # Remove the prefix 'data:image/jpeg;base64,'
    base64_data = data_uri.split(",")[1]
    img_data = base64.b64decode(base64_data)
    img = Image.open(BytesIO(img_data))
    img.show()
    img.save("apify_generated_image.jpg")
    print("✅ Image saved as 'apify_generated_image.jpg'")
else:
    print("⚠️ No image found in response.")
"""
from moviepy import ImageClip
print(ImageClip("video_generator\Apsara pencil\images\scene_1.jpg").resized(lambda t: 1 + 0.05 * t))'''

from mcp.server.fastmcp import FastMCP
import webbrowser
import urllib.parse
 
#create mcp server
mcp = FastMCP("Google search")
 
# add an addition tool
@mcp.tool()
def open_google(query):
    encoded_query=urllib.parse.quote_plus(query)
    url=f"https://www.google.com/search?q={encoded_query}"
    webbrowser.open(url)
 
@mcp.resource("greeting://{name}")
def get_greeting(name:str)->str:
    return f"hello,{name}"
# @mcp.toot()
# def add(a,b):
#     return a+b
@mcp.tool()
def kusumuru_bag():
    c=446
    return f"it contain the 2200 people and {c}cricketers"


