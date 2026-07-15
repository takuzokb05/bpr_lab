"""背景画像生成（Nano Banana Pro / Imagen 4 Fast フォールバック）"""
import io
from pathlib import Path

from google import genai
from google.genai import types

from src.config import MODEL_IMAGE, MODEL_IMAGE_FALLBACK, IMAGE_ASPECT_RATIO


def generate_images(
    client: genai.Client,
    plan: dict,
    output_dir: Path,
) -> list[Path]:
    """
    スライド構成の各 background_prompt から背景画像を生成する。

    Returns:
        生成された画像ファイルパスのリスト（スライド順）
    """
    output_dir = Path(output_dir)
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    image_paths = []
    for slide in plan["slides"]:
        num = slide["slide_number"]
        prompt = slide.get("background_prompt", "")
        if not prompt:
            prompt = "Abstract minimal gradient background, professional, space for text overlay"

        image_path = images_dir / f"slide_{num:03d}.png"

        try:
            # Nano Banana Pro で生成
            _generate_with_nano_banana(client, prompt, image_path)
        except Exception as e:
            print(f"  Nano Banana Pro 失敗（スライド #{num}）: {e}")
            try:
                # Imagen 4 Fast にフォールバック
                _generate_with_imagen(client, prompt, image_path)
                print(f"  → Imagen 4 Fast で代替生成成功")
            except Exception as e2:
                print(f"  Imagen 4 Fast も失敗（スライド #{num}）: {e2}")
                # 画像なし（PPTX ビルダーが単色背景で代替）
                image_path = None

        image_paths.append(image_path)

    return image_paths


def _generate_with_nano_banana(
    client: genai.Client,
    prompt: str,
    save_path: Path,
) -> None:
    """Nano Banana Pro で画像生成"""
    response = client.models.generate_content(
        model=MODEL_IMAGE,
        contents=f"Generate a 16:9 widescreen background image: {prompt}",
        config=types.GenerateContentConfig(
            response_modalities=["image"],
        ),
    )

    # レスポンスから画像データを抽出して保存
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            save_path.write_bytes(part.inline_data.data)
            return

    raise RuntimeError("レスポンスに画像データが含まれていません")


def _generate_with_imagen(
    client: genai.Client,
    prompt: str,
    save_path: Path,
) -> None:
    """Imagen 4 Fast で画像生成（フォールバック）"""
    response = client.models.generate_images(
        model=MODEL_IMAGE_FALLBACK,
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio=IMAGE_ASPECT_RATIO,
            person_generation="dont_allow",
        ),
    )

    if response.generated_images:
        save_path.write_bytes(response.generated_images[0].image.image_bytes)
    else:
        raise RuntimeError("画像が生成されませんでした")


def regenerate_single_image(
    client: genai.Client,
    prompt: str,
    save_path: Path,
) -> Path:
    """単一画像を再生成する（F6 リライト用）"""
    try:
        _generate_with_nano_banana(client, prompt, save_path)
    except Exception:
        _generate_with_imagen(client, prompt, save_path)
    return save_path
