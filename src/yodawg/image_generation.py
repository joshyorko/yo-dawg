
import base64
import sys
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

class YoDawgImageGenerator:
    def __init__(self, model="o3-mini"):
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
    #    + stronger Xzibit likeness
    # ─────────────────────────────────────────
    def build_image_prompt(self, caption: str) -> str:
        """
        Accepts the two-line caption (joined by `|||`) and inserts
        each half into top/bottom Impact text. Adds precise visual
        cues so the generator nails Xzibit’s look. Uses vertical aspect ratio and explicit overflow instructions per OpenAI docs.
        """
        try:
            top, bottom = [p.strip() for p in caption.split("|||", 1)]
        except ValueError:
            top, bottom = caption.strip(), ""

        return (
            "Create a 1024×1792 vertical 'Yo Dawg' meme (extra vertical space helps text fit). "
            "Subject: rapper **Xzibit (Alvin Joiner)**—photorealistic, braided cornrows, thin goatee, "
            "diamond‑stud earrings, studio headphones, big grin, thumbs‑up. "
            "Setting: neon‑lit tech control room with code on multiple monitors.\n\n"
            # --- TEXT RULES ---
            "The TOP caption MUST ALWAYS start with 'YO DAWG'. Place the TOP caption exactly as:\n"
            f'"{top}"\n'
            "and the BOTTOM caption exactly as:\n"
            f'"{bottom}"\n'
            "Use bold white Impact font with black outline. "
            "→ If either line would overflow, **automatically reduce font size or wrap onto a second row** "
            "so all words stay fully inside the frame. Do not crop text.\n\n"
            # --- VISUAL ---
            "Keep the meme layout classic: top text, image, bottom text. "
            "Vibrant blue‑purple lighting, high contrast, sharp focus."
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

    def truncate_and_rewrap(self, caption, max_len=80):
        """
        Truncate and rewrap top/bottom lines to max_len characters.
        """
        try:
            top, bottom = [p.strip() for p in caption.split("|||", 1)]
        except ValueError:
            top, bottom = caption.strip(), ""
        def shorten(line):
            return line[:max_len] + ("…" if len(line) > max_len else "")
        return f"{shorten(top)}|||{shorten(bottom)}"

    def generate_yo_dawg_quote(self, yo_dawg_content):
        prompt = self.build_caption_prompt(yo_dawg_content)
        resp = self.get_chat_completion(prompt)
        caption = self.extract_caption_from_response(resp)
        # Hard cap: 80 chars per line (OpenAI docs & tests show DALLE handles this cleanly)
        try:
            top, bottom = [p.strip() for p in caption.split("|||", 1)]
        except ValueError:
            top, bottom = caption.strip(), ""
        if any(len(line) > 80 for line in (top, bottom)):
            caption = self.truncate_and_rewrap(caption, max_len=80)
        return caption

    def generate_image(self, yo_dawg_caption, output_path):
        image_prompt = self.build_image_prompt(yo_dawg_caption)
        image_base64 = self.generate_image_base64(image_prompt)
        if image_base64:
            self.save_image(image_base64, output_path)
        else:
            print("No image generated.")
