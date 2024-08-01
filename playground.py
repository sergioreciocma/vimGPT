# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.2
#   kernelspec:
#     display_name: OCA Py 3.12
#     language: python
#     name: py_oca
# ---

# %%
import base64
import json
import os
from io import BytesIO

from dotenv import load_dotenv
from PIL import Image
import torch
from xvfbwrapper import Xvfb

from playwright.async_api import async_playwright, Playwright

from transformers import (
    AutoTokenizer,
    AutoProcessor,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline
)

# %%
MODEL_ID = "microsoft/Phi-3-vision-128k-instruct"

processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True) 

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map="cuda",
    trust_remote_code=True,
    _attn_implementation="flash_attention_2"
)

# %%
generation_args = { 
    "max_new_tokens": 100, 
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
    Can you tell what's in the image?
    <|end|>\n
    <|assistant|>
    """

# %%
screenshot = Image.open('www.google.com.png')
objective = 'pass'

inputs = processor(
    prompt.format(objective=objective),
    images=[screenshot],
    return_tensors="pt"
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

# %%
response

# %%
async def run(playwright: Playwright):
    context = await playwright.chromium.launch_persistent_context(
        "",
        headless=False,
        args=[
            f"--disable-extensions-except={vimium_path}",
            f"--load-extension={vimium_path}",
        ],
    )
    
    page = await context.new_page()
    await page.goto('https://www.scrapethissite.com/pages/simple/', wait_until="domcontentloaded")
    
    await page.keyboard.press("Escape")
    await page.keyboard.type("f")
    
    await page.wait_for_timeout(5)
    
    await page.screenshot(path='f1.png')

vimium_path = "vimium-master"

display = Xvfb(width=1920, height=1080)
display.start()
async with async_playwright() as playwright:
    await run(playwright)

# %%
import json

json.loads('{"type": "Open link in current tab.", "click": "Accept all"}')

# %%
