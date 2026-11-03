
import asyncio
import fitz
from pathlib import Path
from chrome_lens_py import LensAPI

# ---------------- CONFIG ----------------

PDF_PATH = Path("C:/Users/tasin/code/shibir-prep/documents/সদস্য নোট ৬০ টি.pdf")

PAGE_NUMBER = 5       # যে পৃষ্ঠা পরীক্ষা করবে (1-based)
DPI = 300

OUTPUT_DIR = Path("ocr_test")
IMAGE_DIR = OUTPUT_DIR / "images"
TEXT_DIR = OUTPUT_DIR / "texts"

# তোমার Chrome Lens API initialization
api = LensAPI()

# ----------------------------------------


def convert_page_to_image(pdf_path, page_number):
    """Convert one PDF page into a high-resolution image."""

    doc = fitz.open(pdf_path)

    if page_number < 1 or page_number > len(doc):
        raise ValueError(f"PDF has only {len(doc)} pages.")

    page = doc[page_number - 1]

    pix = page.get_pixmap(
        matrix=fitz.Matrix(DPI / 72, DPI / 72),
        alpha=False
    )

    image_path = IMAGE_DIR / f"page_{page_number}.png"
    pix.save(str(image_path))

    doc.close()

    return image_path


async def run_ocr(image_path, language):
    """Run OCR using Chrome Lens."""

    result = await api.process_image(
        image_path=str(image_path),
        ocr_language=language
    )

    return result.get("ocr_text", "").strip()


async def main():

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    TEXT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Converting PDF page {PAGE_NUMBER} to image...")

    image_path = convert_page_to_image(
        PDF_PATH,
        PAGE_NUMBER
    )

    print(f"Image saved: {image_path}")

    # Test Bangla and Arabic separately
    for language in ["bn", "ar"]:

        print(f"\nRunning OCR: {language}")

        try:
            ocr_text = await run_ocr(image_path, language)

            output_file = TEXT_DIR / (
                f"page_{PAGE_NUMBER}_{language}.txt"
            )

            output_file.write_text(
                ocr_text,
                encoding="utf-8"
            )

            print(f"Saved: {output_file}")
            print("\n--- OCR RESULT ---\n")
            print(ocr_text[:2000])

        except Exception as error:
            print(f"OCR failed for {language}: {error}")


if __name__ == "__main__":
    asyncio.run(main())
