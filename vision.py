import base64
import boto3
import json
import os

from io import BytesIO
from dotenv import load_dotenv
from PIL import Image


load_dotenv()
IMG_RES = 1080


def init_model():
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="eu-west-2",
    )
    return bedrock_runtime

# Function to encode the image
def encode_and_resize(image):
    W, H = image.size
    image = image.resize((IMG_RES, int(IMG_RES * H / W)))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded_image


def get_actions(screenshot, objective, model):
    #encoded_screenshot = encode_and_resize(screenshot)
    
    prompt = f"""
        <goal>
        You need to choose which actions to take to help a user do this task: {objective}.
        </goal>
        
        <formatting>
        You must respond in JSON only with no other fluff or bad things will happen. The JSON keys must only be TYPE, CLICK or DONE. Do not return the JSON inside a code block.
        </formatting>
        
        <instructions>
        You need to choose amongst the following actions to reach your <goal>: TYPE, CLICK, DONE.
        
        Pay attention to the characters within the yellow boxes, as those will tell you where to click.
        
        If you want to CLICK something to reach your <goal>: return CLICK as the key, and the yellow character sequence on top of the element you want to click.
        If you want to TYPE something to reach your <goal>: return CLICK as the key with the yellow character sequence on top of the writing box, and also return TYPE as key with the message to write.
        If <goal> is DONE: return DONE as a key with no value.
        
        For clicks, please only respond with the 1-2 letter sequence in the yellow box, and if there are multiple valid options choose the one you think a user would select.
        For typing, please return a click to click on the box along with a type with the message to write.
        When the page seems satisfactory, return done as a key with no value.
        </instructions>
        """
    
    encoded_image = encode_and_resize(screenshot)
    
    prompt_config = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "system": "You are a bot made to navigate the web.",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": encoded_image,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "temperature": 0.5,
        }

    body = json.dumps(prompt_config)

    modelId = "anthropic.claude-3-sonnet-20240229-v1:0"
    accept = "application/json"
    contentType = "application/json"

    response = model.invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=contentType
    )

    response_body = json.loads(response.get("body").read())

    results = response_body.get("content")[0].get("text")
    
    try:
        json_response = json.loads(results)
    except json.JSONDecodeError:
        print("Could not parse JSON")

    return json_response


if __name__ == "__main__":
    image = Image.open("image.png")
    actions = get_actions(image, "upvote the pinterest post")
