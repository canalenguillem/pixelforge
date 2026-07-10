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

OUTPUT_PREFIX = "photorestore/restored"
INPAINT_PREFIX = "photorestore/inpaint"

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
