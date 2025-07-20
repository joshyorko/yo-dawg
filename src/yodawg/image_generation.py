
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

    # ─────────────────────────────────────────
    # 1. Funnier, zero‑parrot caption prompt
    # ─────────────────────────────────────────
    def build_caption_prompt(self, content: str) -> str:
        """
        Few‑shot prompt: returns TWO lines separated by `|||`.
        The split lets the image prompt lay out classic top/bottom meme text cleanly.
        """
        return (
            "You are Xzibit, supreme master of recursive Yo‑Dawg memes.\n\n"
            "STYLE RULES\n"
            "• Format **exactly** two lines, separated by '|||'.\n"
            "• Line‑1 starts with 'YO DAWG, I heard you like …'.\n"
            "• Line‑2 delivers the recursive punchline.\n"
            "• Do **not** copy sentences from the source. Compress it to the main concept.\n"
            "• ≤ 100 characters per line. Hyperbole & tech jargon welcome.\n"
            "• No hashtags, no author names, no LinkedIn references.\n\n"
            "EXAMPLES\n"
            "Input: Just finished migrating our CI/CD pipeline to GitHub Actions.\n"
            "Output: YO DAWG, I heard you like pipelines|||so I put a deploy in your deploy so you ship while you ship!\n\n"
            "Input: Deploying a Kubernetes cluster on Raspberry Pi in my homelab tonight.\n"
            "Output: YO DAWG, I heard you like tiny clusters|||so I put a Pi in your k8s so you kube while you kube!\n\n"
            "Input: I wrote 10k lines of Terraform to spin up infra.\n"
            "Output: YO DAWG, I heard you like infra code|||so I put HCL in your HCL so you plan while you apply!\n\n"
            f"NOW TRANSFORM THIS POST:\n\"{content}\"\n"
            "Return exactly two lines separated by '|||'."
        )

    def get_chat_completion(self, prompt):
        return self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )

    def extract_caption_from_response(self, response):
        return response.choices[0].message.content.strip()

    # ─────────────────────────────────────────
    # 2. Image prompt that respects the split
    # ─────────────────────────────────────────
    def build_image_prompt(self, caption: str) -> str:
        """
        Accepts the two‑line caption (joined by `|||`) and inserts
        each half into top/bottom Impact text.
        """
        try:
            top_text, bottom_text = [part.strip() for part in caption.split("|||", 1)]
        except ValueError:
            # Fallback if the model didn’t use the delimiter
            top_text, bottom_text = caption.strip(), ""
        return (
            "Generate a 'Yo Dawg' meme featuring rapper Xzibit grinning with headphones, "
            "inside a futuristic control room glowing blue‑purple. Multiple monitors show code. "
            "Xzibit gives a thumbs‑up toward the camera.\n\n"
            f"TOP TEXT: '{top_text}'\n"
            f"BOTTOM TEXT: '{bottom_text}'\n\n"
            "Use bold white Impact font, adjust size/wrapping so all words are fully visible. "
            "Maintain an energetic, tech‑savvy vibe."
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
