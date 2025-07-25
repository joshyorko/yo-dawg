

import base64
import sys
import os
import time
from dotenv import load_dotenv
from openai import OpenAI
# For static image overlay
from PIL import Image, ImageDraw, ImageFont

class YoDawgImageGenerator:
    def overlay_quote_on_static_image(self, caption, static_image_path, output_path, font_path=None):
        """
        Overlay the Yo Dawg meme caption (split by '|||') on a static image, using meme-style font.
        :param caption: Meme caption, two lines separated by '|||'.
        :param static_image_path: Path to the static image file (e.g., PNG of Xzibit).
        :param output_path: Path to save the new meme image.
        :param font_path: Optional path to a .ttf font file. If not provided, tries bundled font, then system fonts.
        """
        import re
        # Only remove <think> blocks if present
        if '<think>' in caption:
            cleaned_caption = re.sub(r'<think>.*?</think>', '', caption, flags=re.DOTALL)
        else:
            cleaned_caption = caption
        # Remove any lines that do not start with 'YO DAWG' or are not after the split
        if '|||' in cleaned_caption:
            meme_lines = [p.strip() for p in cleaned_caption.split('|||', 1)]
        else:
            # Try to find the YO DAWG line and punchline
            lines = [line.strip() for line in cleaned_caption.splitlines() if line.strip()]
            top = next((l for l in lines if l.upper().startswith('YO DAWG')), lines[0] if lines else '')
            bottom = next((l for l in lines if l != top), '')
            meme_lines = [top, bottom]
        top, bottom = meme_lines if len(meme_lines) == 2 else (meme_lines[0], "")
        # Load image
        img = Image.open(static_image_path).convert("RGBA")
        draw = ImageDraw.Draw(img)
        # Font setup
        font = None
        font_size = 80
        font_candidates = []
        font_path_used = None
        if font_path:
            font_candidates.append(font_path)
        bundled_font = os.path.join(os.path.dirname(__file__), "impact.ttf")
        if os.path.exists(bundled_font):
            font_candidates.append(bundled_font)
        anton_font = os.path.join(os.path.dirname(__file__), "Anton-Regular.ttf")
        if os.path.exists(anton_font):
            font_candidates.append(anton_font)
        font_candidates.append("/usr/share/fonts/truetype/impact/impact.ttf")
        font_candidates.append("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
        font_candidates.append("C:/Windows/Fonts/impact.ttf")
        font_candidates.append("/Library/Fonts/Impact.ttf")
        font_candidates.append("/Library/Fonts/Arial Black.ttf")
        for candidate in font_candidates:
            try:
                font = ImageFont.truetype(candidate, font_size)
                font_path_used = candidate
                break
            except Exception:
                continue
        if font is None:
            font = ImageFont.load_default()
            font_path_used = None
        # Text settings
        def draw_text(text, y, font, img, draw):
            max_width = img.width - 40  # 20px margin on each side
            font_size_local = font.size if hasattr(font, 'size') else 80
            w = None
            while font_size_local > 10:
                bbox = draw.textbbox((0, 0), text, font=font)
                w = bbox[2] - bbox[0]
                if w <= max_width:
                    break
                font_size_local -= 4
                if font_path_used:
                    try:
                        font = ImageFont.truetype(font_path_used, font_size_local)
                    except Exception:
                        font = ImageFont.load_default()
                else:
                    font = ImageFont.load_default()
            if w is None:
                bbox = draw.textbbox((0, 0), text, font=font)
                w = bbox[2] - bbox[0]
            x = (img.width - w) // 2
            outline_range = 4
            for ox in range(-outline_range, outline_range+1):
                for oy in range(-outline_range, outline_range+1):
                    draw.text((x+ox, y+oy), text, font=font, fill="black")
            draw.text((x, y), text, font=font, fill="white")
        # Top text
        draw_text(top, 40, font, img, draw)
        # Bottom text
        draw_text(bottom, img.height - 140, font, img, draw)
        img.save(output_path)
        print(f"Static meme saved to {output_path}")
        # ---
        # To use a custom font, place a .ttf file (e.g., impact.ttf or Anton-Regular.ttf) in the same directory as this script,
        # or provide the font_path argument. If no meme-style font is found, falls back to system fonts or PIL default.
    def __init__(self, model="ollama:gemma3:latest"):
        load_dotenv()
        # Support Ollama via OpenAI API compatibility
        if model and str(model).startswith("ollama:"):
            # Example: model="ollama:llama2"
            self.model = model.split(":", 1)[1]
            self.client = OpenAI(base_url="http://192.168.1.112:11434/v1", api_key="ollama")
        else:
            self.model = model
            self.client = OpenAI()

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
