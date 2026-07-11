# PixelForge — Ideas y features futuras

> Cuaderno de ideas para retomar más adelante. No implementado; notas para
> arrancar rápido sin releer todo el historial. (Anotado: 2026-07-11)

El objetivo del proyecto es **portfolio/aprendizaje**: lo valioso es demostrar
que sé **orquestar cualquier modelo** bajo un producto real (multi-motor, async,
integración de servicio GPU externo). Cada "pestaña/modo" nuevo = otro
`workflow_mode` + su builder → refuerza justamente eso.

---

## Cómo se añade un modo nuevo (patrón ya usado con Epic/Flux/Inpaint)

1. **`backend/app/services/workflows.py`** → `build_<algo>_workflow(...)` que
   devuelve el dict en formato API de ComfyUI.
2. **`backend/app/workers/tasks.py`** → enrutar en `process_restoration_job`
   (o una tarea nueva) y pasar params.
3. **`backend/app/schemas/job.py`** + **`job_service.enqueue_*`** → nuevos params.
4. **`endpoints/jobs.py`** → pasar los params.
5. **Frontend** `ProcessPanel.tsx` (o pestaña nueva) → UI + `job.service.ts`.
6. **Prototipar SIEMPRE primero** con un script contra ComfyUI (ver
   `comfyui_service`: `upload_image`, `submit_prompt`, `run_with_progress`,
   `download_image`, `list_loras`) y ver el resultado antes de cablear.

---

## Ideas de pestañas nuevas (por wow / esfuerzo)

### 1. 🎬 Dar vida / Animar foto (EL WOW)
Foto (restaurada) → **vídeo corto 2-4s** con movimiento sutil. "Living photo".
- **Modelos ya instalados:** `svd_xt.safetensors` / `svd.safetensors` (Stable
  Video Diffusion, img→vídeo), **AnimateDiff** + motion loras, **frame
  interpolation** (comfyui-frame-interpolation) para suavizar.
- **Reto:** salida es vídeo (mp4/webm) → nuevo tipo de resultado, storage y
  reproductor en la UI. VideoHelperSuite ayuda a codificar.
- **Impacto:** máximo. Integrar img→vídeo demuestra mucho rango. Esfuerzo medio-alto.

### 2. 🎨 Estilos / "Reimagina"
Foto → anime / cartoon-Disney / óleo, **preservando composición** con ControlNet.
- **Modelos:** SDXL `novaAnimeXL_xlV10` (anime), `disneyrealcartoonmix_v10`
  (cartoon), `hyphoriaIlluNAI_v001` (Illustrious); ControlNet **depth SDXL**
  (`controlnet-depth-sdxl-1.0`) + `DepthAnythingV2Preprocessor`.
- **Prototipo ya probado** (anime, img2img denoise 0.8 + depth cn 0.7, ~2min):
  funcionó y quedó decente; falta afinar estilo/denoise. Ver el script de
  referencia usado (scratchpad de la sesión) — resultado en `foto_test/anime_nova.png`.
- Esfuerzo medio.

### 3. 🧑‍🎤 Avatares / personajes (identidad preservada)
"Conviértete en personaje / otra época / headshot pro" desde una foto.
- **Modelos:** **PhotoMaker** y **IPAdapter** (`ComfyUI_IPAdapter_plus`) — ya
  instalados; preservan la cara.
- Muy compartible. Esfuerzo medio.

### 4. ✂️ Quitar fondo
Recortar personas / fondo transparente.
- **Modelos:** carpeta `background_removal`, **SAM2** (`segment-anything-2`),
  `sams/sam_vit_b`.
- Práctico y **rápido**. Salida PNG con alpha. Esfuerzo bajo.

### 5. 🖼️ Generar (txt2img) con Z-Image Turbo  ✅ RECETA PROBADA
Pestaña "describe y genera", muy rápida (9 pasos). **Prototipo funcionando** —
resultado en `foto_test/zimage_out.png` (calidad fotorrealista muy alta).

**Grafo correcto (del workflow oficial `image_z_image_turbo.json`):**
```
UNETLoader(z_image_bf16.safetensors, default)
  -> ModelSamplingAuraFlow(shift=3.0)         # ← CRÍTICO, si falta VAEDecode peta
CLIPLoader(qwen_3_4b.safetensors, type="lumina2")   # ← lumina2, NO qwen_image
VAELoader(ae.safetensors)                     # ← el VAE de Flux, NO qwen_image_vae
CLIPTextEncode(clip, prompt)  -> pos
ConditioningZeroOut(pos)      -> neg          # negativo (cfg=1)
EmptySD3LatentImage(1024,1024,1)
KSampler(model=ModelSampling, steps=9, cfg=1.0,
         sampler="res_multistep", scheduler="simple", denoise=1.0)
VAEDecode -> SaveImage
```
- **Es GENERADOR** (txt2img), no editor tipo Kontext → para restaurar NO aporta;
  para **generar** sí. Su gracia: rápido (9 pasos). Carga en frío ~5min (qwen_3_4b
  4B + z_image ~12GB en 16GB → swapping); en caliente, segundos.
- Nota: `TextEncodeZImageOmni` (con `image1/2/3`) es para la variante **edición/omni**.
  **PROBADO y NO funciona con `z_image_bf16`** → produce ruido (`foto_test/zimage_edit.png`).
  Requiere el checkpoint **Z-Image-Omni/Edit** (no instalado). Para EDITAR fotos,
  **Kontext sigue siendo el tool**; Z-Image aquí = solo txt2img.
- Esfuerzo bajo-medio (es txt2img sin upload → endpoint/tarea nuevos).

### 6. ↔️ Expandir / Outpaint
Extender bordes de fotos con encuadre apretado.
- Flux/SDXL + inpaint (ya tienes `comfyui-inpaint-nodes`, Inpaint-CropAndStitch).
- Esfuerzo medio.

---

## Pendientes menores del producto actual

- **Presets de restauración** (en vez de números): `Fiel` (Flux denoise 0.65,
  HDR off) · `Equilibrado` (0.8, HDR off) · `Máxima` (1.0, HDR on). Aprendido:
  para **escenas de calle** va mejor 0.8 + HDR off (a 1.0+HDR se sobreprocesa);
  para **retratos/daño fuerte**, 1.0 + HDR on.
- **README de portfolio** (lo que más rinde): arquitectura + decisiones técnicas
  + capturas/GIFs + "batallitas" (CPU sin AVX→Mongo 4.4, async Celery+WS, ComfyUI
  como API HTTP no SSH, LaMa pixel-exacto, denoise 0.9→1.0, etc.).
- **Histórico en MongoDB** (`jobs_history`): guardar workflow/respuesta/metadatos.
- **Config ComfyUI por usuario** (tabla `comfyui_config`) + API keys LLM (Fernet).
- **Endpoints stub**: `users` (perfil/password), `settings`. Falta un endpoint de
  cambio de contraseña (ahora se hace a mano en BD).

---

## Inventario de modelos en ComfyUI (192.168.1.46) — referencia rápida

- **Restauración (en uso):** Flux Kontext `flux1-kontext-dev-Q6_K.gguf` +
  `clip_l`+`t5xxl_fp8_e4m3fn_scaled` + `ae.safetensors` + LoRA
  `F.1_realistic_HDR_v1`; SD1.5 `epicrealism` + Tile ControlNet + CodeFormer +
  `RealESRGAN_x2`; inpaint `big-lama`.
- **SDXL:** novaAnimeXL, disneyrealcartoonmix, epicrealismXL, juggernautXL,
  autismmixPony, sd_xl_base_1.0, hyphoriaIlluNAI (Illustrious). LoRAs SDXL de
  ilustración/cartoon en `loras/sdxl/`.
- **Vídeo:** svd, svd_xt (SVD), AnimateDiff + motion loras, frame interpolation.
- **Identidad/segmentación:** PhotoMaker, IPAdapter, SAM2, background_removal.
- **ControlNet:** SD1.5 (tile, lineart, openpose, scribble, depth) y SDXL
  (depth, t2i-openpose). Preprocesadores: Canny, LineArt, AnimeLineArt,
  DepthAnythingV2 (controlnet_aux).
- **Generación:** Z-Image (`z_image_bf16`, `z_image-Q8_0`) + qwen encoders.

> Recordatorio: ComfyUI está en otra máquina y **puede estar apagado** —
> verificar `curl http://192.168.1.46:8188/system_stats` antes de nada.
