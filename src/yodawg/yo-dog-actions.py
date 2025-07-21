from time import sleep


from sema4ai.actions import action, Response, ActionError
import os
from .image_generation import YoDawgImageGenerator
from .models import YoDawgResponse
from typing import Optional


from robocorp import browser
from sema4ai.actions import action, Response, ActionError
import os
from .image_generation import YoDawgImageGenerator
from .models import YoDawgResponse
import time
import dotenv
from typing import Optional

dotenv.load_dotenv()


LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")



# ─────────────────────────────────────────
# New action: Overlay Yo Dawg quote on a static image
# ─────────────────────────────────────────


@action
def set_browser_context() -> Response:
    """
    Logs into LinkedIn, pauses for a specified number of seconds, and returns a Response indicating login success.
    :param pause_seconds: Number of seconds to pause after login (default: 5).
    """
    configure_browser(headless_mode=False)
    page = browser.goto("https://www.linkedin.com/login")
    # Fill in username and password using environment variables
    if LINKEDIN_USERNAME is None or LINKEDIN_PASSWORD is None:
        page.close()
        raise ActionError("LinkedIn credentials are not set in environment variables.")
    page.get_by_role("textbox", name="Email or phone").fill(LINKEDIN_USERNAME)
    page.get_by_role("textbox", name="Password").fill(LINKEDIN_PASSWORD)
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.pause()


    page.close()
    return Response(result=f"LinkedIn login successful.")
    

def _overlay_yo_dawg_quote_on_static_image(
    yo_dawg_content: str,
    static_image_path: str,
    output_path: Optional[str] = None,
    model: Optional[str] = None
) -> YoDawgResponse:
    """
    Overlay a generated Yo Dawg meme caption on a static image.
    :param yo_dawg_content: Content to generate the meme caption from.
    :param static_image_path: Path to the static image file.
    :param output_path: Path to save the new meme image (optional, auto-generated if not provided).
    :param model: Optional model name for caption generation.
    """
    if not yo_dawg_content:
        raise ActionError("No content provided for meme caption generation.")
    if not static_image_path or not os.path.exists(static_image_path):
        raise ActionError(f"Static image not found: {static_image_path}")
    generator = YoDawgImageGenerator(model=model) if model else YoDawgImageGenerator()
    yo_caption = generator.generate_yo_dawg_quote(yo_dawg_content)
    if not yo_caption:
        raise ActionError("Failed to generate Yo Dawg caption.")
    if not output_path:
        images_dir = "yo-dawg-images"
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        output_path = os.path.join(images_dir, f"yo_dawg_static_{int(time.time())}.png")
    generator.overlay_quote_on_static_image(yo_caption, static_image_path, output_path)
    yo_dawg_response = YoDawgResponse(caption=yo_caption, image_filename=output_path)
    return yo_dawg_response

# ─────────────────────────────────────────
# New action: Generate only Yo Dawg quote from content
# ─────────────────────────────────────────
@action
def generate_yo_dawg_quote_only(
    yo_dawg_content: str,
    model: Optional[str] = None
) -> Response:
    """
    Generate only the Yo Dawg meme caption from the provided content, using the specified model (if any).
    :param yo_dawg_content: The content to transform into a Yo Dawg meme caption.
    :param model: Optional model name to use for generation.
    """
    if not yo_dawg_content:
        raise ActionError("No content provided for meme caption generation.")
    generator = YoDawgImageGenerator(model=model) if model else YoDawgImageGenerator()
    yo_caption = generator.generate_yo_dawg_quote(yo_dawg_content)
    if not yo_caption:
        raise ActionError("Failed to generate Yo Dawg caption.")
    return Response(result=yo_caption)


@action
def rich_mans_yo_dawg_comment(
    post_url: Optional[str] = None,
    custom_context: Optional[str] = None,
    append_custom_context: bool = False
) -> Response:
    """
    Generate and post a Yo Dawg meme comment on LinkedIn by creating a new image.
    Uses one of three modes:
    1. Only LinkedIn post content (provide post_url)
    2. Only custom context (provide custom_context)
    3. LinkedIn post content with appended custom context (provide both, set append_custom_context=True)
    
    :param post_url: The URL of the LinkedIn post to comment on.
    :param custom_context: Optional custom context string for meme generation.
    :param append_custom_context: If True, append custom context to LinkedIn post content.
    """
    return _comment_on_linkedin(
        post_url=post_url,
        custom_context=custom_context,
        append_custom_context=append_custom_context,
        use_rich_man_mode=True
    )



@action
def poor_mans_yo_dawg_comment(
    post_url: Optional[str] = None,
    custom_context: Optional[str] = None,
    append_custom_context: bool = False,
    model: Optional[str] = None,
    image_path: Optional[str] = None,
) -> Response:
    """
    Generate and post a Yo Dawg meme comment on LinkedIn by overlaying text on a static image.
    Uses one of three modes:
    1. Only LinkedIn post content (provide post_url)
    2. Only custom context (provide custom_context)
    3. LinkedIn post content with appended custom context (provide both, set append_custom_context=True)
    
    :param post_url: The URL of the LinkedIn post to comment on.
    :param custom_context: Optional custom context string for meme generation.
    :param append_custom_context: If True, append custom context to LinkedIn post content.
    :param model: Optional model name for meme caption generation (supports OpenAI and Ollama).
    :param image_path: Optional path to an existing image to post directly, bypassing meme generation.
    (Uses static image path hardcoded in generator logic.)
    """
    return _comment_on_linkedin(
        post_url=post_url,
        custom_context=custom_context,
        append_custom_context=append_custom_context,
        use_rich_man_mode=False,
        model=model,
        image_path=image_path,
    )


def _comment_on_linkedin(
    post_url: Optional[str],
    custom_context: Optional[str],
    append_custom_context: bool,
    use_rich_man_mode: bool,
    model: Optional[str] = None,
    image_path: Optional[str] = None,
) -> Response:
    """
    Internal function to handle commenting logic for both rich and poor man's versions.
    """
    page = None  # Initialize page to None
    meme_context: Optional[str] = None

    # Logic for handling inputs
    if image_path:
        if not post_url:
            raise ActionError("post_url must be provided when using image_path.")
        if not os.path.exists(image_path):
            raise ActionError(f"Image not found at specified path: {image_path}")
    else:
        if append_custom_context:
            if not post_url or not custom_context:
                raise ActionError("Both post_url and custom_context must be provided when append_custom_context is True.")
        elif custom_context and not post_url:
            meme_context = custom_context
        elif post_url and not custom_context:
            pass  # meme_context will be fetched from post
        elif post_url and custom_context:
            raise ActionError("If you want to append custom context, set append_custom_context=True. Otherwise, provide only one.")
        else:
            raise ActionError("You must provide either post_url, custom_context, or both with append_custom_context=True.")

    # Browser and page handling
    if post_url:
        configure_browser()
        page = browser.goto(post_url)

    # Meme generation if no image_path is provided
    if not image_path:
        if post_url and page:
            post_content = get_linkedin_post_content(page)
            if append_custom_context and custom_context:
                meme_context = f"{post_content}\n\n{custom_context}"
            else:
                meme_context = post_content
        
        if not meme_context:
            raise ActionError("No context available for meme generation.")

        # Generate meme based on mode
        if use_rich_man_mode:
            yo_dawg_response = yo_dawg_generator(meme_context)
        else:
            # Hardcode static image path for poor man's mode
            static_image_path = "templates/GtGTtP_WIAAHKqP.jpg"
            yo_dawg_response = _overlay_yo_dawg_quote_on_static_image(meme_context, static_image_path, model=model)
        
        image_path = yo_dawg_response.image_filename

    signature = (
        "\n— Generated by Yo Dawg Action Server | Sema4.ai · MCP‑powered"
    )
    comment_text = signature
    
    if post_url and page:
        # Click on the comment box
        page.get_by_role("textbox", name="Text editor for creating").get_by_role("paragraph").click()
        # Add image if provided
        if image_path and os.path.exists(image_path):
            print(f"Uploading image: {image_path}")
            try:
                with page.expect_file_chooser() as fc_info:
                    page.locator("button[aria-label*='photo']").click()
                file_chooser = fc_info.value
                file_chooser.set_files(image_path)
                page.wait_for_selector("img[alt*='Image preview']", timeout=10_000)
                print("Image uploaded and preview is visible.")
            except Exception as e:
                print(f"Could not upload image: {str(e)}")
        else:
            print(f"Image not found or path empty: {image_path}")
        # Add the comment text
        page.get_by_role("textbox", name="Text editor for creating").fill(comment_text)
        # Submit the comment
        print("Submitting comment...")
        page.locator("button[class^='comments-comment-box__submit-button']").click()
        time.sleep(10)
        page.close()
        result_message = f"Commented on post: {post_url}"
        if image_path:
            result_message += f" with image: {image_path}"
        result_message += f" (Generated Yo Dawg meme)"
    else:
        result_message = f"Generated Yo Dawg meme with custom context only."
        if image_path:
            result_message += f" Image: {image_path}"
    return Response(result=result_message)


def get_linkedin_post_content(page) -> str:
    """
    Get the content text from a LinkedIn post page.
    
    :param page: The browser page object already navigated to the LinkedIn post.
    :return: The post content as a string.
    """
    try:
        # Try to find the main post content - updated selector
        post_content = page.locator(".update-components-text").first.inner_text()
        return post_content
    except Exception as e:
        # Fallback selectors
        try:
            post_content = page.locator("[data-test-id='main-feed-activity-card'] .feed-shared-text").first.inner_text()
            return post_content
        except Exception as e2:
            try:
                post_content = page.locator(".feed-shared-text").first.inner_text()
                return post_content
            except Exception as e3:
                return "this post"  # fallback content


def yo_dawg_generator(
    yo_dawg_content: str,
) -> YoDawgResponse:
    """
    A 'Yo Dawg' action that generates a meme caption and image.
    """
    try:
        if not yo_dawg_content:
            raise ActionError("No content provided for meme generation.")

        generator = YoDawgImageGenerator()
        yo_caption = generator.generate_yo_dawg_quote(yo_dawg_content)
        if not yo_caption:
            raise ActionError("Failed to generate Yo Dawg caption.")

        images_dir = "yo-dawg-images"
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        unique_filename = f"yo_dawg_image_{int(time.time())}.png"
        image_path = os.path.join(images_dir, unique_filename)
        generator.generate_image(yo_caption, image_path)

        return YoDawgResponse(caption=yo_caption, image_filename=image_path)
    except Exception as e:
        raise ActionError(f"An error occurred: {str(e)}")



def configure_browser(headless_mode: bool = True):
    browser.configure(
        screenshot="only-on-failure",
        headless=headless_mode,
        persistent_context_directory=os.path.join(os.getcwd(), "browser_context"),

    )




def _is_authenticated(page):
    # Try to find an element that only appears when logged in, e.g., the profile avatar or "Me" menu
    try:
        # This selector may need adjustment based on LinkedIn's DOM
        page.get_by_role("navigation").get_by_text("Me", exact=True, timeout=3000)
        return True
    except Exception:
        return False
