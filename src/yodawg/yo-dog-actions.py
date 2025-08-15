from time import sleep


from sema4ai.actions import action, Response, ActionError
import os
from .image_generation import YoDawgImageGenerator
from .models import YoDawgResponse
from typing import Optional
from .signature import build_signature


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
def set_browser_context(headless_mode: bool = True) -> Response:
    """
    Logs into LinkedIn, pauses for a specified number of seconds, and returns a Response indicating login success.
    :param headless_mode: Whether to run the browser in headless mode (default: True).
    """
    configure_browser(headless_mode=headless_mode)
    page = browser.goto("https://www.linkedin.com/login")
    # Fill in username and password using environment variables
    if LINKEDIN_USERNAME is None or LINKEDIN_PASSWORD is None:
        page.close()
        raise ActionError("LinkedIn credentials are not set in environment variables.")
    page.get_by_role("textbox", name="Email or phone").fill(LINKEDIN_USERNAME)
    page.get_by_role("textbox", name="Password").fill(LINKEDIN_PASSWORD)
    page.get_by_role("button", name="Sign in", exact=True).click()
    time.sleep(5)  # Wait for login to complete

    page.close()
    return Response(result=f"LinkedIn login successful.")
    

def _overlay_yo_dawg_quote_on_static_image(
    yo_dawg_content: str,
    static_image_path: str,
    output_path: Optional[str] = None,
    model: str = None
) -> YoDawgResponse:
    """
    Overlay a generated Yo Dawg meme caption on a static image.
    :param yo_dawg_content: Content to generate the meme caption from.
    :param static_image_path: Path to the static image file.
    :param output_path: Path to save the new meme image (optional, auto-generated if not provided).
    :param model: Model name for caption generation (required).
    """
    if not yo_dawg_content:
        raise ActionError("No content provided for meme caption generation.")
    if not static_image_path or not os.path.exists(static_image_path):
        raise ActionError(f"Static image not found: {static_image_path}")
    if not model:
        raise ActionError("Parameter 'model' is required and must be provided.")
    generator = YoDawgImageGenerator(model=model)
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
    model: str,
) -> Response:
    """
    Generate only the Yo Dawg meme caption from the provided content, using the specified model.
    :param yo_dawg_content: The content to transform into a Yo Dawg meme caption.
    :param model: Model name to use for generation. Required.
    """
    if not yo_dawg_content:
        raise ActionError("No content provided for meme caption generation.")
    if not model:
        raise ActionError("Parameter 'model' is required and must be provided.")
    generator = YoDawgImageGenerator(model=model)
    yo_caption = generator.generate_yo_dawg_quote(yo_dawg_content)
    if not yo_caption:
        raise ActionError("Failed to generate Yo Dawg caption.")
    return Response(result=yo_caption)


@action
def rich_mans_yo_dawg_comment(
    model: str,
    post_url: Optional[str] = None,
    custom_context: Optional[str] = None,
    append_custom_context: bool = False,
    head_mode: bool = True
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
    :param model: Model name for meme caption/image generation (required).
    :param head_mode: Whether to run the browser in headless mode (default: True). Set to False to see the browser UI during execution.
    """
    if not model:
        raise ActionError("Parameter 'model' is required and must be provided.")
    return _comment_on_linkedin(
        post_url=post_url,
        custom_context=custom_context,
        append_custom_context=append_custom_context,
        use_rich_man_mode=True,
        model=model,
        head_mode=head_mode
    )



@action
def poor_mans_yo_dawg_comment(
    model: str,
    post_url: Optional[str] = None,
    custom_context: Optional[str] = None,
    append_custom_context: bool = False,
    image_path: Optional[str] = None,
    head_mode: bool = True
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
    :param model: Model name for meme caption generation (supports OpenAI and Ollama). Required.
    :param image_path: Optional path to an existing image to post directly, bypassing meme generation.
    (Uses static image path hardcoded in generator logic.)
    :param head_mode: Whether to run the browser in headless mode (default: True). Set to False to see the browser UI during execution.
    """
    if not model:
        raise ActionError("Parameter 'model' is required and must be provided.")
    return _comment_on_linkedin(
        post_url=post_url,
        custom_context=custom_context,
        append_custom_context=append_custom_context,
        use_rich_man_mode=False,
        model=model,
        image_path=image_path,
        head_mode=head_mode
    )


def _comment_on_linkedin(
    post_url: Optional[str],
    custom_context: Optional[str],
    append_custom_context: bool,
    use_rich_man_mode: bool,
    model: Optional[str] = None,
    image_path: Optional[str] = None,
    head_mode: bool = True
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
        configure_browser(headless_mode=head_mode)
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
            if not model:
                raise ActionError("Parameter 'model' is required for rich man mode.")
            yo_dawg_response = yo_dawg_generator(meme_context, model)
        else:
            # Hardcode static image path for poor man's mode
            static_image_path = "templates/GtGTtP_WIAAHKqP.jpg"
            if not model:
                raise ActionError("Parameter 'model' is required for poor man mode.")
            yo_dawg_response = _overlay_yo_dawg_quote_on_static_image(meme_context, static_image_path, model=model)
        
        image_path = yo_dawg_response.image_filename

    # Build signature (always executed, independent of image generation branch)
    mode_str = "rich" if use_rich_man_mode else "poor"
    comment_text = build_signature(mode=mode_str, model=model)
    
    if post_url and page:
        # Click on the comment box (disambiguate element to avoid strict-mode errors)
        try:
            editor = page.get_by_role("textbox", name="Text editor for creating").first
            editor.click()
        except Exception:
            # Fallback: click the first visible contenteditable region
            editor = page.locator("[contenteditable='true']").first
            editor.click()
        # Small wait to ensure the editor is ready
        page.wait_for_timeout(300)

        # Find the nearest composer container to scope subsequent actions
        try:
            container = editor.locator(
                "xpath=ancestor::*[contains(@class,'comments-comment-box') or contains(@class,'comments-comment-item')]"
            ).first
            # Ensure it's present; if not, fallback to page
            if container.count() == 0:
                container = page
        except Exception:
            container = page

        # Add image if provided
        if image_path and os.path.exists(image_path):
            print(f"Uploading image: {image_path}")
            try:
                with page.expect_file_chooser() as fc_info:
                    container.locator("button[aria-label*='Add a photo'], button[aria-label*='photo']").first.click()
                file_chooser = fc_info.value
                file_chooser.set_files(image_path)
                # Wait for a reasonable preview indicator to appear
                page.wait_for_selector(
                    "img[alt*='preview'], img[alt*='Image'], [data-test-media-urn], img[class*='comments-media']",
                    timeout=15000,
                )
                print("Image uploaded and preview is visible.")
            except Exception as e:
                print(f"Could not upload image: {str(e)}")
        else:
            print(f"Image not found or path empty: {image_path}")

        # Add the comment text (use the same disambiguated locator)
        try:
            page.get_by_role("textbox", name="Text editor for creating").first.fill(comment_text)
        except Exception:
            page.locator("[contenteditable='true']").first.fill(comment_text)

        # Submit the comment
        print("Submitting comment...")
        try:
            # Prefer submit within the same composer container
            submit_btn = container.locator(
                "button.comments-comment-box__submit-button, button[class*='comments-comment-box__submit-button']"
            ).first
            submit_btn.wait_for(state="visible", timeout=5000)
            submit_btn.click()
        except Exception:
            # Fallback to Ctrl+Enter in the editor
            try:
                editor.press("Control+Enter")
            except Exception:
                # Last resort: click any visible submit button on the page
                page.locator(
                    "button.comments-comment-box__submit-button, button[class*='comments-comment-box__submit-button']"
                ).first.click()
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
    model: str,
) -> YoDawgResponse:
    """
    A 'Yo Dawg' action that generates a meme caption and image.
    """
    try:
        if not yo_dawg_content:
            raise ActionError("No content provided for meme generation.")

        generator = YoDawgImageGenerator(model=model)
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
