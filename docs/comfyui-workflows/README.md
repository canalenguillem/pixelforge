# Workflows de ComfyUI (para vídeo / demo)

Estos son los workflows **exactos** que ejecuta la app PixelForge, exportados al
**formato API** de ComfyUI. Sirven para mostrar en ComfyUI cómo funciona la
restauración por dentro, antes de enseñar la app web.

| Fichero | Modo en la app | Nodos clave |
|---------|----------------|-------------|
| `epic_restoration.api.json` | **Epic** (rápido) | CheckpointLoader (epicrealism) → ImageScale → VAEEncode → **Tile ControlNet** → KSampler (denoise 0.35) → VAEDecode → **RealESRGAN x2** → **CodeFormer** (caras) → SaveImage |
| `flux_restoration.api.json` | **Flux · calidad** | UnetLoaderGGUF (kontext) + DualCLIP + VAE → FluxKontextImageScale → VAEEncode → CLIPTextEncode → **ReferenceLatent** → **FluxGuidance** → **HDR LoRA** → KSampler (cfg 1, 30 steps) → VAEDecode → RealESRGAN x2 → SaveImage |

## Cómo cargarlos en ComfyUI

1. Abre ComfyUI (tu instancia en `192.168.1.46:8188`).
2. **Menú → Workflow → Open** (o arrastra el `.json` al lienzo). ComfyUI 0.21+
   detecta el formato API y **reconstruye el grafo** (auto-organiza los nodos).
3. En el nodo **LoadImage** verás `example.jpg` (placeholder): selecciona tu foto.
4. Pulsa **Queue** para ejecutarlo.

> Si tu versión de ComfyUI no reconstruye el grafo desde formato API:
> - Para **Flux**, usa directamente el workflow **UI** que compraste
>   (`Photo_restoration_kontext_v1.json`, en la raíz) — es la misma lógica y se
>   ve perfecto.
> - Para **Epic**, pídeme una versión en formato UI y te la genero.

## Modelos que usan (ya instalados en tu ComfyUI)

- **Epic**: `epicrealism.safetensors`, `control_v11f1e_sd15_tile_fp16` (SD1.5),
  `codeformer.pth` (+ pesos de detección), `RealESRGAN_x2.pth`.
- **Flux**: `flux1-kontext-dev-Q6_K.gguf`, `clip_l` + `t5xxl_fp8_e4m3fn_scaled`,
  `ae.safetensors`, `F.1_realistic_HDR_v1.safetensors` (LoRA HDR), `RealESRGAN_x2.pth`.

## Diferencias vs. lo que ejecuta la app

Son idénticos salvo dos detalles que la app rellena en tiempo real:
- El **nombre de la imagen** (LoadImage) lo pone la app tras subir la foto a ComfyUI.
- Las **dimensiones** del ImageScale (Epic) se calculan según cada foto (aquí van
  fijadas a un ejemplo 3:2). El resto (modelos, prompts, sampler, LoRA) es igual.

Los prompts curados de Flux (B&N y Colorizar) están en
`backend/app/services/workflows.py` (`FLUX_PROMPT_BW` / `FLUX_PROMPT_COLOR`).
