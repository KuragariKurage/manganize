from io import BytesIO

from langchain.chat_models import init_chat_model
from PIL import Image

from manganize.agents import ManganizeAgent

agent = ManganizeAgent(model=init_chat_model(model="google_genai:gemini-3-pro-preview"))


def main():
    result = agent(
        # (
        #     Path(
        #         "/mnt/c/Users/atsu/Documents/obsidian/clippings/Post-Training Generative Recommenders with Advantage-Weighted Supervised Finetuning.md"
        #     )
        # ).read_text(),
        "https://unsloth.ai/blog/r1-reasoning",
        thread_id="1",
    )

    if result.get("generated_image"):
        image = Image.open(BytesIO(result.get("generated_image")))
        image.save("generated_image.png")


if __name__ == "__main__":
    main()
