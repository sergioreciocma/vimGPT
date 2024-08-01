import base64
import json
import os
from io import BytesIO

from dotenv import load_dotenv
from PIL import Image
import torch

from transformers import (
    AutoTokenizer,
    AutoProcessor,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline
)

load_dotenv()
MODEL_ID = "microsoft/Phi-3-vision-128k-instruct"
IMG_RES = 1080


def init_model(model_id):
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True) 

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        trust_remote_code=True,
        _attn_implementation="flash_attention_2"
    )
    
    return processor, model


# Function to encode the image
def encode_and_resize(image):
    W, H = image.size
    image = image.resize((IMG_RES, int(IMG_RES * H / W)))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded_image


def get_actions(screenshot, objective, processor, model):
    #encoded_screenshot = encode_and_resize(screenshot)
    
    generation_args = { 
        "max_new_tokens": 500, 
        "temperature": 0.2, 
        "do_sample": True, 
    }
       
    prompt = r"""
        <|system|>
        You are a bot made to navigate the web.
        <|end|>\n
        <|user|>
        You need to choose which action to take to help a user do this task: {objective}. Your options are navigate, type, click, and done. Navigate should take you to the specified URL. Type and click take strings where if you want to click on an object, return the string with the yellow character sequence you want to click on, and to type just a string with the message you want to type. For clicks, please only respond with the 1-2 letter sequence in the yellow box, and if there are multiple valid options choose the one you think a user would select. For typing, please return a click to click on the box along with a type with the message to write. When the page seems satisfactory, return done as a key with no value. You must respond in JSON only with no other fluff or bad things will happen. The JSON keys must ONLY be one of navigate, type, or click. Do not return the JSON inside a code block.
        <|image_1|>
        <|end|>\n
        <|assistant|>
        """

    inputs = processor(
        prompt, images=[screenshot], return_tensors="pt"
    ).to("cuda:0")

    generate_ids = model.generate(
        **inputs,
        eos_token_id=[processor.tokenizer.eos_token_id, 32001, 32007], # included several stop tokens otherwise model doesn't stop responding until limit reached
        **generation_args
    ) 

    # remove input tokens 
    generate_ids_response = generate_ids[:, inputs['input_ids'].shape[1]:]
    response = processor.batch_decode(
        generate_ids_response,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0] 

    return response


if __name__ == "__main__":
    image = Image.open("image.png")
    actions = get_actions(image, "upvote the pinterest post")
