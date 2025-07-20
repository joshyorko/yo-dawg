
from pydantic import Field
from sema4ai.actions import Response


class YoDawgResponse(Response):
    caption: str = Field(..., description="The generated Yo Dawg meme caption.")
    image_filename: str = Field(..., description="The filename of the generated meme image.")