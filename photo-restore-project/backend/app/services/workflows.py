"""Constructores de workflows de ComfyUI (formato API /prompt).

Un workflow API es un dict {node_id: {class_type, inputs}}. Las conexiones
entre nodos se expresan como [node_id, output_index].

Pipeline de restauración (fiel, sin alterar composición):
    1. Escalar a la resolución de trabajo de SD1.5 (lado largo ~1024).
    2. img2img con `epicrealism` guiado por Tile ControlNet a denoise bajo
       -> reenfoca, limpia grano y textura preservando la estructura.
    3. RealESRGAN x2 -> resolución final.
    4. CodeFormer -> restauración de caras.

El `denoise` es la "fuerza de restauración": más alto limpia más (incl. manchas)
pero altera identidad/detalles; más bajo es más fiel. Sweet spot ~0.30-0.38.
"""

from typing import Any

# Modelos disponibles en el ComfyUI del usuario (verificados vía /object_info).
CHECKPOINT = "epicrealism.safetensors"
UPSCALE_MODEL = "RealESRGAN_x2.pth"
FACERESTORE_MODEL = "codeformer.pth"
TILE_CONTROLNET = "SD1.5\\control_v11f1e_sd15_tile_fp16.safetensors"
FACE_DETECTION = "retinaface_resnet50"
INPAINT_MODEL = "big-lama.pt"

# --- Flux Kontext (GGUF) ---
FLUX_UNET_GGUF = "flux1-kontext-dev-Q6_K.gguf"
FLUX_CLIP_L = "clip_l.safetensors"
FLUX_CLIP_T5 = "t5xxl_fp8_e4m3fn_scaled.safetensors"
FLUX_VAE = "ae.safetensors"
# LoRA HDR (opcional): dale realismo/rango dinámico. Se activa con la keyword "HDR"
# en el prompt (por eso ambos prompts terminan en HDR). Si no está instalada en
# ComfyUI, el worker lo detecta y la ignora sin romper.
FLUX_HDR_LORA = "F.1_realistic_HDR_v1.safetensors"

OUTPUT_PREFIX = "photorestore/restored"
INPAINT_PREFIX = "photorestore/inpaint"
FLUX_PREFIX = "photorestore/flux"
STYLE_PREFIX = "photorestore/style"

# --- Z-Image Turbo (estilos rápidos, img2img) ---
ZIMAGE_UNET = "z_image_bf16.safetensors"
ZIMAGE_CLIP = "qwen_3_4b.safetensors"  # cargado con type="lumina2"
ZIMAGE_VAE = "ae.safetensors"

# Presets de estilo (clave -> prompt). El img2img preserva la composición;
# el prompt solo aporta el ESTILO.
STYLE_PRESETS: dict[str, str] = {
    "oleo": "vibrant oil painting, impressionist style, thick expressive brush strokes, warm artistic colors, fine art masterpiece",
    "acuarela": "soft watercolor painting, delicate washes, flowing pastel colors, hand-painted, light and airy, artistic",
    "anime": "anime illustration, cel shading, clean line art, vibrant saturated colors, detailed anime artwork",
    "comic": "comic book illustration, bold black ink outlines, halftone shading, vivid saturated colors, pop art style",
    "lapiz": "detailed graphite pencil sketch, hand-drawn, fine cross-hatching, monochrome drawing, sketchbook",
    "acrilico": "colorful acrylic painting, bold vivid strokes, textured canvas, contemporary art",
}
DEFAULT_STYLE = "oleo"

# Prompts curados (adaptados del workflow de referencia): instrucciones de edición
# para Flux Kontext, muy explícitas en PRESERVAR identidad/composición.
FLUX_PROMPT_BW = (
    "Change the photographic damage, cracks and scratches of the image to a fully "
    "restored, pristine, high quality black and white photograph "
    "| Keep the people's facial features, hair, clothes, accessories, poses, "
    "expressions and the original composition unchanged "
    "| Preserve every subject's identity, camera angle and framing exactly "
    "| Adjust the black and white tones for a clear and natural appearance "
    "| Remove brightness spots and fingerprints, HDR"
)
FLUX_PROMPT_COLOR = (
    "Change the photographic damage, cracks, scratches and monochrome coloration of "
    "the image to a fully restored, pristine, colorized photograph "
    "| Keep the people's facial features, hair, clothes, accessories, poses, "
    "expressions and the original composition unchanged "
    "| Preserve every subject's identity, camera angle and framing exactly "
    "| Apply realistic colorization to skin tones, hair, clothing and background "
    "for a natural appearance "
    "| Remove brightness spots and fingerprints, HDR"
)

DEFAULT_POSITIVE = (
    "restored vintage black and white photograph, monochrome, sharp focus, "
    "fine detail, clean, high quality, realistic, natural skin texture, clear fabric"
)
DEFAULT_NEGATIVE = (
    "stains, brown spots, water damage, scratches, dust, creases, fold, blur, "
    "low quality, noise, discoloration, jpeg artifacts, deformed, colorful, oversaturated"
)

# Resolución de trabajo del pase de difusión (lado largo). SD1.5 rinde mejor ~1024.
WORK_LONG_SIDE = 1024


def work_dimensions(width: int, height: int, long_side: int = WORK_LONG_SIDE) -> tuple[int, int]:
    """Dimensiones de trabajo (múltiplo de 8) manteniendo el aspecto."""
    if width >= height:
        w = long_side
        h = int(round(height * long_side / width / 8) * 8)
    else:
        h = long_side
        w = int(round(width * long_side / height / 8) * 8)
    return max(8, w - (w % 8)), max(8, h - (h % 8))


def build_restoration_workflow(
    image_name: str,
    work_width: int,
    work_height: int,
    denoise: float = 0.35,
    codeformer_fidelity: float = 0.5,
    cn_strength: float = 0.9,
    steps: int = 20,
    cfg: float = 7.0,
    seed: int = 42,
    positive: str = DEFAULT_POSITIVE,
    negative: str = DEFAULT_NEGATIVE,
) -> dict[str, Any]:
    """Workflow de restauración fiel para una imagen ya subida a ComfyUI."""
    return {
        "load": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "scale": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["load", 0],
                "upscale_method": "lanczos",
                "width": work_width,
                "height": work_height,
                "crop": "disabled",
            },
        },
        "ckpt": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": CHECKPOINT},
        },
        "pos": {"class_type": "CLIPTextEncode", "inputs": {"text": positive, "clip": ["ckpt", 1]}},
        "neg": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["ckpt", 1]}},
        "cnet": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": TILE_CONTROLNET}},
        "cn": {
            "class_type": "ControlNetApplyAdvanced",
            "inputs": {
                "positive": ["pos", 0],
                "negative": ["neg", 0],
                "control_net": ["cnet", 0],
                "image": ["scale", 0],
                "strength": cn_strength,
                "start_percent": 0.0,
                "end_percent": 1.0,
            },
        },
        "enc": {"class_type": "VAEEncode", "inputs": {"pixels": ["scale", 0], "vae": ["ckpt", 2]}},
        "ks": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["ckpt", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "positive": ["cn", 0],
                "negative": ["cn", 1],
                "latent_image": ["enc", 0],
                "denoise": denoise,
            },
        },
        "dec": {"class_type": "VAEDecode", "inputs": {"samples": ["ks", 0], "vae": ["ckpt", 2]}},
        "upm": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": UPSCALE_MODEL}},
        "ups": {
            "class_type": "ImageUpscaleWithModel",
            "inputs": {"upscale_model": ["upm", 0], "image": ["dec", 0]},
        },
        "frm": {"class_type": "FaceRestoreModelLoader", "inputs": {"model_name": FACERESTORE_MODEL}},
        "fr": {
            "class_type": "FaceRestoreCFWithModel",
            "inputs": {
                "facerestore_model": ["frm", 0],
                "image": ["ups", 0],
                "facedetection": FACE_DETECTION,
                "codeformer_fidelity": codeformer_fidelity,
            },
        },
        "save": {
            "class_type": "SaveImage",
            "inputs": {"images": ["fr", 0], "filename_prefix": OUTPUT_PREFIX},
        },
    }


def build_restoration_flux_workflow(
    image_name: str,
    denoise: float = 1.0,
    colorize: bool = False,
    use_hdr_lora: bool = False,
    guidance: float = 2.5,
    steps: int = 30,
    seed: int = 42,
    positive: str | None = None,
) -> dict[str, Any]:
    """Workflow de restauración con Flux Kontext (GGUF) — calidad superior.

    Flux Kontext es un modelo de EDICIÓN por instrucción: la imagen original se
    aporta como referencia (ReferenceLatent) y el prompt describe la restauración.
    A `denoise` alto (~0.85-1.0) restaura de verdad preservando a las personas;
    por debajo de 0.5 apenas cambia. cfg=1 + FluxGuidance (Flux no usa CFG clásico).

    - colorize: usa el prompt de colorización (si no, restaura en B&N).
    - use_hdr_lora: aplica la LoRA HDR (el worker resuelve si está instalada).

    Nota: mucho más lento y pesado que Epic (~14 GB en VRAM).
    """
    if positive is None:
        positive = FLUX_PROMPT_COLOR if colorize else FLUX_PROMPT_BW

    wf: dict[str, Any] = {
        "unet": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": FLUX_UNET_GGUF}},
        "clip": {
            "class_type": "DualCLIPLoader",
            "inputs": {"clip_name1": FLUX_CLIP_L, "clip_name2": FLUX_CLIP_T5, "type": "flux"},
        },
        "vae": {"class_type": "VAELoader", "inputs": {"vae_name": FLUX_VAE}},
        "load": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "scale": {"class_type": "FluxKontextImageScale", "inputs": {"image": ["load", 0]}},
        "encode": {"class_type": "VAEEncode", "inputs": {"pixels": ["scale", 0], "vae": ["vae", 0]}},
        "pos": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": positive}},
        "ref": {
            "class_type": "ReferenceLatent",
            "inputs": {"conditioning": ["pos", 0], "latent": ["encode", 0]},
        },
        "guide": {
            "class_type": "FluxGuidance",
            "inputs": {"conditioning": ["ref", 0], "guidance": guidance},
        },
        "neg": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["pos", 0]}},
        "ks": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["unet", 0],
                "seed": seed,
                "steps": steps,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "positive": ["guide", 0],
                "negative": ["neg", 0],
                "latent_image": ["encode", 0],
                "denoise": denoise,
            },
        },
        "dec": {"class_type": "VAEDecode", "inputs": {"samples": ["ks", 0], "vae": ["vae", 0]}},
        "upm": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": UPSCALE_MODEL}},
        "ups": {
            "class_type": "ImageUpscaleWithModel",
            "inputs": {"upscale_model": ["upm", 0], "image": ["dec", 0]},
        },
        "save": {
            "class_type": "SaveImage",
            "inputs": {"images": ["ups", 0], "filename_prefix": FLUX_PREFIX},
        },
    }

    # HDR LoRA opcional (el worker ya ha verificado que está instalada).
    if use_hdr_lora and FLUX_HDR_LORA:
        wf["lora"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {"model": ["unet", 0], "lora_name": FLUX_HDR_LORA, "strength_model": 1.0},
        }
        wf["ks"]["inputs"]["model"] = ["lora", 0]

    return wf


def build_zimage_style_workflow(
    image_name: str,
    work_width: int,
    work_height: int,
    prompt: str,
    denoise: float = 0.5,
    steps: int = 14,
    seed: int = 42,
) -> dict[str, Any]:
    """Estiliza una imagen con Z-Image Turbo (img2img): óleo, anime, etc.

    img2img (VAEEncode + denoise) preserva la composición y reestiliza; el
    `denoise` (0.4-0.7) controla cuánta libertad tiene el estilo. Rápido.
    Grafo del workflow oficial de Z-Image Turbo (lumina2 CLIP + ae VAE +
    ModelSamplingAuraFlow + res_multistep).
    """
    return {
        "unet": {"class_type": "UNETLoader", "inputs": {"unet_name": ZIMAGE_UNET, "weight_dtype": "default"}},
        "sampling": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["unet", 0], "shift": 3.0}},
        "clip": {"class_type": "CLIPLoader", "inputs": {"clip_name": ZIMAGE_CLIP, "type": "lumina2", "device": "default"}},
        "vae": {"class_type": "VAELoader", "inputs": {"vae_name": ZIMAGE_VAE}},
        "load": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "scale": {
            "class_type": "ImageScale",
            "inputs": {"image": ["load", 0], "upscale_method": "lanczos", "width": work_width, "height": work_height, "crop": "disabled"},
        },
        "enc": {"class_type": "VAEEncode", "inputs": {"pixels": ["scale", 0], "vae": ["vae", 0]}},
        "pos": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": prompt}},
        "neg": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["pos", 0]}},
        "ks": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["sampling", 0], "seed": seed, "steps": steps, "cfg": 1.0,
                "sampler_name": "res_multistep", "scheduler": "simple",
                "positive": ["pos", 0], "negative": ["neg", 0],
                "latent_image": ["enc", 0], "denoise": denoise,
            },
        },
        "dec": {"class_type": "VAEDecode", "inputs": {"samples": ["ks", 0], "vae": ["vae", 0]}},
        "save": {"class_type": "SaveImage", "inputs": {"images": ["dec", 0], "filename_prefix": STYLE_PREFIX}},
    }


def build_inpaint_workflow(image_name: str, mask_name: str, grow: int = 8) -> dict[str, Any]:
    """Workflow de eliminación de daño (manchas/arañazos) con LaMa.

    Rellena SOLO la zona enmascarada (blanco) por textura circundante y compone
    sobre el original, de modo que el resto queda pixel a pixel intacto.

    - image_name / mask_name: ficheros ya subidos a ComfyUI (input/).
    - grow: píxeles de expansión de la máscara (cubre bordes de la mancha).
    """
    return {
        "load": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "mask": {
            "class_type": "LoadImageMask",
            "inputs": {"image": mask_name, "channel": "red"},
        },
        "grow": {
            "class_type": "GrowMask",
            "inputs": {"mask": ["mask", 0], "expand": grow, "tapered_corners": True},
        },
        "model": {
            "class_type": "INPAINT_LoadInpaintModel",
            "inputs": {"model_name": INPAINT_MODEL},
        },
        "inpaint": {
            "class_type": "INPAINT_InpaintWithModel",
            "inputs": {
                "inpaint_model": ["model", 0],
                "image": ["load", 0],
                "mask": ["grow", 0],
                "seed": 0,
            },
        },
        "composite": {
            "class_type": "ImageCompositeMasked",
            "inputs": {
                "destination": ["load", 0],
                "source": ["inpaint", 0],
                "mask": ["grow", 0],
                "x": 0,
                "y": 0,
                "resize_source": False,
            },
        },
        "save": {
            "class_type": "SaveImage",
            "inputs": {"images": ["composite", 0], "filename_prefix": INPAINT_PREFIX},
        },
    }
