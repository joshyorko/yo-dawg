
import base64
import sys
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

class YoDawgImageGenerator:
    def __init__(self, model="gpt-4.1"):
        load_dotenv()
        self.client = OpenAI()
        self.model = model

    def build_caption_prompt(self, content):
        return (
            "Create a 'Yo Dawg' meme caption based on this content.\n"
            "Follow the classic format: 'Yo dawg, I heard you like [X], so I put [X] in your [Y] so you can [X] while you [X]!'\n"
            f"Content: \"{content}\"\nYo Dawg Caption:"
        )

    def get_chat_completion(self, prompt):
        return self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )

    def extract_caption_from_response(self, response):
        return response.choices[0].message.content.strip()

    def build_image_prompt(self, caption):
        return (
            f"Create a 'Yo Dawg' meme image with the following text overlay: '{caption}'. "
            f"The image should show Xzibit, a smiling Black man with headphones in a high-tech control room or office setting "
            f"with multiple computer monitors showing code/data in the background. He should be giving a thumbs up. "
            f"The text should be in large white bold letters at the top and bottom of the image in classic meme format. "
            f"Make sure all text is fully visible and not cut off; adjust font size and placement as needed to fit the caption within the image boundaries. "
            f"If the caption is long, use smaller font or wrap text as needed to keep all words inside the image. "
            f"The overall style should be modern, tech-focused, and energetic with blue/purple lighting."
        )

    def generate_image_base64(self, prompt):
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            tools=[{"type": "image_generation"}],
        )
        image_data = [
            output.result
            for output in response.output
            if output.type == "image_generation_call"
        ]
        return image_data[0] if image_data else None

    def save_image(self, image_base64, path):
        with open(path, "wb") as f:
            f.write(base64.b64decode(image_base64))
        print(f"Image saved to {path}")

    def generate_yo_dawg_quote(self, yo_dawg_content):
        prompt = self.build_caption_prompt(yo_dawg_content)
        resp = self.get_chat_completion(prompt)
        content = self.extract_caption_from_response(resp)
        return content

    def generate_image(self, yo_dawg_caption, output_path):
        image_prompt = self.build_image_prompt(yo_dawg_caption)
        image_base64 = self.generate_image_base64(image_prompt)
        if image_base64:
            self.save_image(image_base64, output_path)
        else:
            print("No image generated.")
