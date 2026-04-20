---
name: write-meshy-prompts
description: Create production-ready Meshy prompts and workflow guidance for Text to 3D, Image to 3D references, texture/retexture prompts, game assets, riggable humanoid characters, 3D print models, export choices, and Meshy troubleshooting. Use when the user asks for Meshy prompts, AI 3D asset prompts, Meshy Image-to-3D reference prompts, game/print/rigging prompt packs, texture prompts, or help improving Meshy generation results.
---

# Write Meshy Prompts

## Skill Operating Checklist

Use this checklist before writing any Meshy prompt or Meshy workflow answer:

- Classify the requested output: Text to 3D model, Image to 3D reference image, texture, retexture, riggable character, game asset, 3D print model, troubleshooting, or production handoff.
- Separate the generation stages: geometry/model prompt, image/reference prompt, texture prompt, and post-generation workflow. Do not merge incompatible goals into one overloaded prompt.
- Ask only for missing constraints that materially change the answer. Otherwise make reasonable assumptions and state them briefly.
- Optimize for the final use case first: game runtime, humanoid rigging, 3D printing, web/GLB, engine export, slicer readiness, or material/texture polish.
- Provide purpose-built prompts in copy-ready text blocks. Include settings and avoid lists when they reduce failure risk.
- If the user asks for both game and print, produce separate prompts for each goal.
- If the user asks about latest Meshy behavior, pricing, API fields, or UI limits, verify from official Meshy sources before giving exact current claims.
- Treat community/Reddit patterns as anecdotal workflow signals, not guaranteed Meshy behavior.
- Preserve text/logo workflows: remove text before mesh generation; add text or logos during texture when possible.
- If the user asks for texture after an existing generated model, assume the texture request applies to that existing asset unless the conversation clearly says otherwise.
- If image-based geometry fidelity matters and the user only has one angle, recommend 3 to 4 separate views and prefer Multi-view over a single-image guess.
- Avoid unsupported or risky prompt structures unless the user explicitly requests them.

## Direct Meshy API Execution

When Meshy API MCP tools are available and the user asks Codex to create, check, download, remesh, retexture, rig, or animate a Meshy asset directly, use the Meshy MCP tools instead of stopping at prompt text. Prefer `meshy_create_text_to_3d_asset_pack` for Text to 3D requests that should create, wait, refine, download, and package an asset in one command. Before paid generation, report the estimated credit cost and continue only after user approval or an explicit `confirm_spend=true`. Keep API keys out of responses and files. Check authentication or balance before diagnosing API failures. For explicit generation requests, submit the task, poll until a terminal status when practical, and return task IDs, status, model URLs, downloaded file paths, and credit usage when available. Do not create paid tasks when the user only asks for a prompt or workflow plan. When a user asks for texture after a recently created asset, default to that asset and prefer `meshy_refine_text_to_3d` or `meshy_retexture` instead of creating a brand-new mesh. When a single image is not enough to preserve side or back shape, ask for separate front, back, and side views and prefer `meshy_create_multi_image_to_3d`.

## Response Shape

Prefer this compact structure and omit sections that do not apply:

```text
Recommended workflow:
[Text to 3D, AI image -> Image to 3D, Multi-view, Texture, Retexture, Remesh, Rig, Print, Export, or cleanup path]

Model prompt:
[geometry-focused Meshy prompt]

Image reference prompt:
[clean single-object image prompt when Image to 3D control is useful]

Texture prompt:
[surface-only prompt when texture, PBR, material, or retexture guidance is useful]

Settings and handoff:
[A/T pose, Image Enhancement, Multi-view, remesh/topology, polycount, file format, engine/slicer checks]

Avoid:
[specific things that would harm this use case]
```

## Decision Rules

- Use Text to 3D for fast concept exploration, draft props, simple stylized assets, and cases where exact silhouette is not critical.
- Use AI image -> Image to 3D when exact shape, controlled style, consistent asset sets, hero props, characters, costumes, or product-like forms matter.
- Use Multi-view when side/back geometry matters. Use separate images of the same object, not a collage.
- If a texture request follows an already generated asset in the same thread, treat it as a follow-up on that asset unless the user explicitly switches targets.
- Prefer `meshy_retexture` for completed textured models and `meshy_refine_text_to_3d` when the active asset is still in the Text to 3D preview/refine flow.
- If the user only provides one reference image for an object whose side/back silhouette matters, recommend 3 to 4 clean angles and move to Multi-view when those images exist.
- Use A-pose or T-pose for humanoid rigging; prefer A-pose unless a target pipeline expects T-pose.
- For riggable characters, prioritize full body, standard humanoid proportions, separated limbs, visible joints, fitted clothing, no cape, no long skirt, no weapon attached.
- For 3D printing, prioritize single solid object, flat stable base, thick printable parts, minimal overhangs, no floating parts, STL or 3MF export, and slicer inspection.
- For game assets, prioritize clean silhouette, material separation, real-time polycount, engine scale/origin checks, GLB for web/simple static use, and FBX for animation/game engines.
- For texture prompts, describe surface only: material, color, wear, roughness, metalness, style consistency. Do not try to change the mesh shape through texture wording.

## Source Completeness

The complete user-provided master guide is embedded below and also preserved verbatim at `references/meshy-prompt-master-guide.md`. Use the embedded guide as the authoritative operating content for this skill. Keep the reference file as the source-preserving copy when updating or checking completeness.

# Meshy Prompt Master Guide

Last updated: 2026-04-20

Purpose: This document is written as a complete operating guide for another AI or prompt assistant. It explains how to create strong Meshy prompts for 3D game assets, riggable characters, 3D print models, image-to-3D references, texture generation, retexturing, and production handoff.

Important scope note: Meshy changes over time. This guide is based on official Meshy Help Center, Meshy Docs/API pages, Meshy blog posts, and anecdotal Reddit/user workflow reports researched in April 2026. Official docs are authoritative. Reddit and community posts are useful practical signals, not guaranteed behavior.

---

## 1. Core Mental Model

Meshy prompt mastery is not one magic prompt. The best results come from separating the problem into distinct generation stages:

1. Geometry prompt
   - Controls the 3D shape, silhouette, anatomy, object parts, pose, and functional form.
   - Best for Text to 3D or when describing the object before creating a reference image.

2. Image/reference prompt
   - Controls the 2D image that will become the 3D model in Image to 3D.
   - This is often the highest-control route for exact shapes and consistent style.

3. Texture prompt
   - Controls surface material, color, pattern, wear, roughness, metallic feel, and PBR-style visual quality.
   - Should not try to change geometry.

4. Post-generation workflow
   - Remesh, resize, set origin, texture edit, rig, animate, export, and test in engine or slicer.

Key rule: Do not mix "model shape", "scene background", "texture detail", "animation", and "printability" into one overloaded prompt. Meshy performs better when each stage has a clear goal.

---

## 2. Official Meshy Constraints And Behavior

### 2.1 Text to 3D

Use Text to 3D when:

- You need quick concept exploration.
- You want many rough ideas fast.
- You do not need exact shape control.
- You are making props, simple characters, creatures, toys, artifacts, furniture, weapons, stylized objects, or draft models.

Official best practices:

- Focus on one object, not a full scene.
- Use about 3 to 6 key descriptive details.
- Be specific and physical.
- Use reference terms like "like motocross gear" or "in the style of an ancient artifact".
- For humanoid rigging, include or select T-pose or A-pose.
- Avoid complex or contradictory descriptions.
- Avoid non-physical effects like smoke, glitter, magic energy, fog, particles, or aura if they may become unwanted geometry.
- Avoid ultra-fine details like individual hair strands.
- Avoid adjective overload.
- Avoid technical jargon the model may not parse correctly.
- Meshy does not support negative prompts in the current UI flow described by the Help Center.

Strong Text to 3D prompt formula:

```text
[single main subject], [clear silhouette/body shape], [3-6 defining details], [material/color], [style/reference], [pose/use case]
```

Example:

```text
Full body humanoid goblin rogue, clear separated arms and legs, fitted leather armor, short hood, oversized ears, green skin, A-pose, stylized low-poly RPG enemy, ready for auto-rigging
```

### 2.2 Image to 3D

Use Image to 3D when:

- You need higher control over shape and visual details.
- You need consistent style across multiple themed models.
- You can create or edit a clean 2D reference first.
- You need a specific silhouette, costume, product shape, or prop design.

Official input recommendations:

- Single clearly defined object.
- Front-facing or angled view, whichever shows the most total geometry detail.
- Plain, white, or simple background.
- High resolution, ideally over 1040 x 1040.
- Well-lit, clean, sharp image.
- Avoid blur, low contrast, busy background, multiple objects, long hair/fine thin details, environmental effects, and too much text in the image.

Best Image to 3D reference image formula:

```text
Single centered [object], full object visible, front-facing or three-quarter view, plain white background, clean studio lighting, sharp readable silhouette, no extra objects, optimized for 3D model generation
```

Example:

```text
Single centered stylized goblin rogue character, full body visible, front-facing view, arms slightly away from torso, legs separated, plain white background, clean studio lighting, sharp readable silhouette, no weapons attached, optimized for 3D model generation
```

### 2.3 Text to Image / AI Image Before Image to 3D

Meshy recommends generating or modifying an AI image first when high control is needed. Use this as the "concept art to 3D" route.

For Image to 3D workflows:

- 1:1 square aspect ratio is often recommended.
- Generate multiple image variations and pick the cleanest one.
- Use reference images to preserve style or shape.
- Use prompt instructions like:
  - "Make this low-poly."
  - "Simplify for 3D printing."
  - "Change the material to gold with cracks in it."
  - "Remove background and change to front-facing angle."
  - "Use the shape from Image 1 and the style from Image 2."

### 2.4 Image Enhancement

Meshy 6 Image Enhancement pre-processes images for cleaner 3D reconstruction.

Keep Image Enhancement ON when:

- Image is noisy, cluttered, AI generated, low resolution, dramatically lit, reflective, text/logo-heavy, or has distracting background elements.
- You want stable, clean, predictable geometry.

Consider turning it OFF when:

- The image is already clean, high-resolution, well-lit, and very readable.
- Meshy is removing/isolating the wrong object.
- You must preserve unusual tiny details, complex surface texture, or original lighting/color influence.

### 2.5 Multi-view

Meshy 6 supports Multi-view for Image to 3D. It can include up to 3 more images, for a total of up to 4 views.

Rules:

- All images must show the same object.
- Use different angles.
- Do not put multiple angles in one image as a collage.
- Do not include multiple objects.
- The order of uploaded images is not important according to Meshy Help.
- This is especially useful for characters and objects where back/side shape matters.

### 2.6 Texture / Retexture

Texture prompts should describe surface, not shape.

Texture prompt formula:

```text
[material], [base color palette], [surface details], [wear/damage], [roughness/metalness], [style consistency]
```

Example:

```text
Weathered dark brown leather, visible grain, small stitches along the seams, worn corners, subtle dust in creases, realistic PBR game asset texture
```

Rules:

- Text Input guides texture by words.
- Image Input guides texture by reference image.
- Meshy Help says negative prompts are not supported for texture prompts.
- PBR maps can be generated.
- Meshy 5 and Meshy 6 can generate textures.
- If both texture prompt and texture image are provided via API, docs say the text prompt is used by default.
- Texture image may not work well if the texture reference and actual geometry are substantially different.

### 2.7 Text And Logos

Problem: If a reference image contains text, Meshy may interpret text as physical geometry, engraving it into the mesh.

Safer workflow:

1. Remove text from the reference image.
2. Generate the mesh from the clean text-free image.
3. Apply text/logo during texturing using the original image.

Result: Text becomes surface texture rather than broken geometry.

### 2.8 A-pose, T-pose, Custom Pose

Meshy supports A/T pose controls for humanoid characters.

Use A-pose when:

- You want more natural shoulder deformation.
- You plan to rig/skinning in many animation pipelines.
- You need a robust default for auto-rigging.

Use T-pose when:

- Your target tool/pipeline expects T-pose.
- You want a traditional rigging reference.

Important:

- A/T pose is designed for humanoid characters.
- If the prompt or reference is not clearly humanoid, results may vary.
- The pose toggle affects pose, not textures/materials.
- T-pose does not work 100 percent of the time; regenerate with a cleaner reference if needed.
- Custom pose can be used with a posed reference image, useful especially for posed character 3D prints.

---

## 3. Game Asset Production System

Goal: Create assets usable in game engines such as Unity, Unreal, Godot, Roblox, Three.js, Babylon.js, or custom WebGL.

Game assets need:

- Clean silhouette.
- Reasonable polycount.
- Readable style from target camera.
- Texture/material separation.
- Engine-compatible export format.
- Correct scale and origin.
- Optional rig/animation support for characters.

### 3.1 Game Asset Decision Tree

If the asset is a simple prop:

- Use Text to 3D for quick generation.
- Use Image to 3D if exact style/shape matters.
- Prompt with "low-poly", "game-ready", "simple geometry", "clean silhouette".

If the asset is a hero prop or weapon:

- Prefer AI Image -> Image to 3D.
- Generate front/three-quarter clean concept art first.
- Texture separately for PBR/material control.

If the asset is a humanoid character that must be riggable:

- Prefer Image to 3D using a clean full-body front/three-quarter reference.
- Use A-pose or T-pose control.
- Prompt for separated limbs, clear anatomy, no cape, no long skirt, no weapon attached.
- Texture before rigging if using Meshy rigging.

If the asset is a creature:

- If rigging in Meshy is needed, keep it bipedal/humanoid.
- If quadruped animation is needed, check current Meshy animation UI capabilities, but API docs currently emphasize humanoid/biped reliability.
- Avoid unusual anatomy unless you plan manual Blender rigging.

### 3.2 Game Prompt Template

```text
[Asset type], [camera/readability requirement], [clear shape/silhouette], [3-5 major parts], [material/color], [style], [optimization target], [pipeline constraint]
```

Example static prop:

```text
Low-poly fantasy health potion bottle, readable from top-down camera, chunky round glass body, cork stopper, thick leather strap, glowing red liquid as texture detail, stylized mobile game asset, simple geometry, clean silhouette, optimized for real-time rendering
```

Example environment prop:

```text
Stylized wooden treasure chest, readable from isometric camera, large metal bands, oversized lock, chunky proportions, hand-painted fantasy texture, low-poly game asset, clean edges, simple geometry, no floating parts
```

Example hero weapon:

```text
Game-ready sci-fi plasma rifle, clear hard-surface silhouette, separate barrel, stock, grip and magazine shapes, brushed gunmetal body, cyan glowing panels as texture detail, medium-poly FPS weapon asset, clean topology, no floating parts
```

### 3.3 Game Asset Keywords

Use when appropriate:

- low-poly
- mobile game asset
- stylized game asset
- game-ready
- simple geometry
- clean silhouette
- readable from top-down camera
- readable from isometric camera
- optimized for real-time rendering
- hard-surface
- chunky proportions
- hand-painted texture
- PBR texture
- clean material separation
- no floating parts
- centered object

Avoid:

- ultra-thin details
- many tiny hanging chains
- smoke/fog/magic aura as geometry
- too many accessories fused into one model
- full scene prompts
- "beautiful", "cool", "epic" without physical descriptors

### 3.4 Game Texture Prompt Templates

Hand-painted stylized:

```text
Hand-painted RPG texture, warm earthy colors, clear material separation between leather, metal and cloth, soft edge highlights, subtle dirt in creases, no dramatic baked shadows, clean game-ready surface
```

Realistic PBR:

```text
Realistic PBR texture, brushed steel plates, worn silver edges, dark leather straps, subtle scratches, balanced roughness, clean material separation, no heavy baked lighting
```

Sci-fi:

```text
Clean sci-fi PBR texture, matte white ceramic armor panels, black rubber joints, cyan emissive line details, subtle edge wear, smooth roughness, no noisy surface clutter
```

Mobile low-poly:

```text
Simple stylized texture, bright readable colors, large painted details, minimal noise, clean material blocks, soft highlights, optimized for mobile game readability
```

### 3.5 Polycount And Remesh Guidance

Meshy API and UI support remesh, topology choices, and target polycount. Remesh can generate triangle or quad-dominant meshes and target formats like GLB, FBX, OBJ, USDZ, BLEND, STL, and 3MF.

Practical rules:

- For mobile props: request/use low-poly, simple geometry, and consider 1k-5k triangles where appropriate.
- For environment modular pieces: lower poly is usually enough, especially for top-down/isometric cameras.
- For hero props: medium poly is acceptable if close-up.
- For characters: keep enough geometry to deform, but reduce excessive face counts before rigging or engine import.
- For rigging via Meshy API with input_task_id, models over 300,000 faces are not supported.
- Use quad topology if further editing in Blender is expected.
- Use triangle/decimated topology for straightforward game engine or print usage.

### 3.6 Game Export Format

From Meshy file format guidance:

- FBX: best for game development when animation, armatures, and broad Unity/Unreal compatibility matter.
- GLB: good for web, Three.js, Babylon.js, simple pipelines, fast loading, and compact all-in-one assets.
- OBJ: useful for simple static geometry or legacy tools, but no animation.
- BLEND: useful if staying in Blender.
- USDZ: Apple AR/Vision Pro.

Recommended:

- Unity character with animations: FBX.
- Unreal character with animations: FBX.
- Roblox rigged/animated: FBX.
- Three.js/WebGL: GLB.
- Static prop for quick preview: GLB.
- Blender editing: FBX, GLB, OBJ, or BLEND depending workflow.

---

## 4. Riggable Character System

Goal: Generate Meshy characters that are more likely to auto-rig and animate cleanly.

### 4.1 Official Rigging Constraints

Meshy API docs say programmatic rigging currently works best with standard humanoid bipedal assets with clearly defined limbs and body structure.

Currently not suitable for:

- Untextured meshes.
- Non-humanoid assets.
- Humanoid assets with unclear limb/body structure.
- Models over 300,000 faces when using input_task_id.

The rigging output can include:

- Rigged character FBX.
- Rigged character GLB.
- Basic walking/running animation URLs, depending task options/defaults.

### 4.2 Riggable Character Prompt Formula

```text
Full body [humanoid/biped character], standard humanoid proportions, clear separated arms and legs, visible shoulders elbows knees hands and feet, symmetrical body, fitted clothing/armor, [short hair/no cape/no long skirt/no weapon attached], A-pose or T-pose, game-ready character for auto-rigging
```

Strong general template:

```text
Full body humanoid game character, standard biped proportions, clear separated arms and legs, visible shoulders, elbows, knees, hands and feet, symmetrical body, fitted outfit, short hair not covering shoulders, no cape, no long skirt, no weapon attached, A-pose, clean readable silhouette, ready for auto-rigging
```

### 4.3 Riggable Character Examples

RPG adventurer:

```text
Full body female adventurer character, standard humanoid proportions, clear separated arms and legs, visible shoulders elbows knees hands and feet, fitted leather armor, simple boots and gloves, short tied hair, no cape, no long skirt, no weapon attached, A-pose, stylized RPG game character, ready for auto-rigging
```

Cyberpunk enemy:

```text
Full body cyberpunk street soldier, standard humanoid proportions, arms separated from torso, legs separated with clear gap, fitted tactical jacket and pants, simple helmet, visible gloves and boots, no cape, no weapon attached, symmetrical body, T-pose, low-poly game enemy, clean silhouette, ready for auto-rigging
```

Biped monster:

```text
Bipedal monster character, humanoid skeleton structure, two arms and two legs, upright stance, clear shoulders and hips, separated limbs, large readable claws, short tail not touching legs, no wings, no extra arms, A-pose, stylized dark fantasy game enemy, ready for auto-rigging
```

Robot:

```text
Full body humanoid robot character, standard biped proportions, clear separated mechanical arms and legs, visible elbow and knee joints, simple shoulder plates, compact torso, no loose cables, no weapon attached, symmetrical body, A-pose, clean sci-fi game character, ready for auto-rigging
```

### 4.4 Riggable Image Reference Prompt

When generating the 2D reference first:

```text
Single centered full body humanoid character, A-pose, arms slightly away from torso, legs separated, front-facing view, symmetrical body, fitted outfit, short hair, no cape, no long skirt, no weapon, plain white background, clean studio lighting, sharp readable silhouette, optimized for 3D auto-rigging
```

### 4.5 Riggable Character Do Not Use

Avoid for auto-rigging:

- Cape, cloak, poncho, robe that hides arms/legs.
- Long skirt or dress merging the legs.
- Long hair covering shoulders, elbows, or back.
- Arms touching torso.
- Legs fused together.
- Weapon attached to hand.
- Shield attached to body.
- Backpack with straps hiding shoulders.
- Tentacles, multiple arms, wings, centaur body, snake tail lower body.
- Dynamic action pose if the goal is rigging.
- Huge shoulder pads blocking upper arms.
- Very high poly models over rigging limits.
- Untextured model for Meshy rigging.

### 4.6 Rigging Workflow

Recommended game character workflow:

1. Generate or prepare a full-body humanoid image reference.
2. Ensure clean front or three-quarter view.
3. Ensure plain background and no extra objects.
4. Use Image to 3D.
5. Enable/select A-pose or T-pose.
6. Inspect mesh for separated limbs and usable anatomy.
7. Texture the model.
8. Remesh if face count is too high.
9. Rig in Meshy Animate/Rig or via API.
10. Apply animations.
11. Export FBX for Unity/Unreal/Roblox or GLB for simpler/web pipeline.
12. Test deformation in engine or Blender.
13. If shoulders/hips deform poorly, regenerate with cleaner limb separation or simpler clothing.

### 4.7 Animation Notes

Meshy Animation API applies an animation action to a successfully rigged character using a rig_task_id and action_id.

Post-processing can:

- Change FPS to 24, 25, 30, or 60.
- Convert FBX to USDZ.
- Extract armature.

Meshy output can include animation GLB and FBX URLs.

For Blender:

- Meshy Help describes exporting multiple animations into a single file.
- In Blender, use Dope Sheet -> Action Editor to switch actions.

---

## 5. 3D Print Production System

Goal: Generate models that can be sliced and printed with minimal cleanup.

3D printing cares about:

- Closed model, no holes/gaps.
- No floating or loose parts.
- Flat and stable base.
- Minimal dangerous overhangs.
- Thick enough details.
- Clean readable silhouette at print scale.
- Support requirements.
- Single solid object unless intentionally multi-part.

Official Meshy 3D printing advice:

- Closed model.
- No floating/loose parts.
- Flat stable base.
- Avoid large overhangs.
- Keep thin details strong.
- Start simple.
- Check/clean in Blender, Meshmixer, or Microsoft 3D Builder after export.
- Preview in slicers such as Cura or Bambu Studio.
- Meshy can add a base via Print options.

### 5.1 3D Print Prompt Formula

```text
Single solid [object/figurine], flat stable base, thick printable parts, no paper-thin details, no floating parts, minimal overhangs, clean silhouette readable at [scale], suitable for [FDM/resin] 3D printing
```

### 5.2 3D Print Examples

FDM desk toy:

```text
Cute robot desk toy, single solid object, flat feet with stable footing, thick arms and antenna, rounded body, no thin wires, no floating parts, minimal overhangs, clean silhouette, suitable for FDM 3D printing
```

Resin miniature:

```text
Tabletop knight miniature, single solid model, heroic standing pose on round base, thick sword and shield attached to the body, sturdy helmet crest, armor details as raised sculpted forms, minimal overhangs, no loose floating parts, readable at 32mm scale, 3D printable resin miniature
```

Dragon statue:

```text
Single solid chibi dragon figurine, flat stable circular base, thick legs and tail connected to the body, short sturdy wings attached to the back, chunky horns, no paper-thin details, no floating parts, clean silhouette readable at small scale, 3D printable toy sculpture
```

Functional holder:

```text
Single solid phone stand, wide flat stable base, thick support arms, rounded edges, simple geometric shape, no thin walls, no floating parts, minimal overhangs, suitable for FDM 3D printing
```

### 5.3 3D Print Image Reference Prompt

For generating an image before Image to 3D:

```text
Single centered [figurine/object], full object visible, plain white background, clean studio lighting, thick printable forms, flat stable base, no thin fragile details, no floating parts, minimal overhangs, sharp readable silhouette, optimized for 3D printing
```

Example:

```text
Single centered cute dragon figurine, full body visible, flat circular base, thick legs, thick tail connected to body, short sturdy wings, plain white background, clean studio lighting, no thin fragile details, no floating parts, optimized for 3D printing
```

### 5.4 Print-Safe Keywords

Use:

- single solid object
- closed model
- flat stable base
- round base
- thick printable parts
- no paper-thin details
- no floating parts
- minimal overhangs
- support-friendly pose
- sturdy limbs
- readable at small scale
- suitable for FDM printing
- suitable for resin printing
- raised sculpted details
- engraved details
- chunky proportions

Avoid:

- T-pose for printing unless intentionally supported.
- Thin swords, thin antennae, thin fingers, thin chains.
- Hair strands.
- Floating magic, smoke, aura, particles.
- Huge wings unsupported.
- Long tail floating away from body.
- Open hollow forms unless intentionally designed.
- Fine texture-only details if printing single color.

### 5.5 Game Character vs Print Character

Same concept, different prompt.

Game riggable goblin:

```text
Full body humanoid goblin rogue, clear separated arms and legs, visible shoulders elbows knees hands and feet, fitted leather armor, short hood not covering shoulders, no cape, no weapon attached, symmetrical body, A-pose, stylized low-poly RPG enemy, ready for auto-rigging
```

3D print goblin:

```text
Single solid goblin rogue figurine, crouching pose on round flat base, thick dagger attached to hand, sturdy ears and nose, chunky readable clothing folds, no floating parts, minimal overhangs, clean silhouette, 3D printable tabletop miniature
```

Reason: Game version exposes skeleton. Print version prioritizes stability and strength.

### 5.6 Print Export Format

Use:

- STL for simple universal geometry-only printing.
- 3MF for color/material/multi-part or modern multi-color printer workflows.

Do not rely on texture for single-color print detail. Convert important visual detail into raised/engraved geometry in prompt.

### 5.7 3D Print Workflow

1. Choose print technology: FDM or resin.
2. Choose scale: e.g. 32mm miniature, 12cm desk toy.
3. Prompt for single solid object, flat base, thick parts.
4. Prefer Image to 3D if exact silhouette matters.
5. Use custom posed reference if making character statue.
6. Avoid rigging pose for print unless needed.
7. Generate and inspect for floating parts, holes, thin walls, fragile pieces.
8. Use Meshy Print/Add Base if helpful.
9. Export STL or 3MF.
10. Open in slicer.
11. Check overhangs, supports, islands, manifold errors, wall thickness, scale.
12. If needed, repair in Blender, Meshmixer, Microsoft 3D Builder, or slicer repair tools.

---

## 6. Image To 3D Master Rules

Image to 3D is usually the highest-control workflow.

The reference image should:

- Show one object only.
- Show the whole object.
- Use front or three-quarter view.
- Have plain white/simple background.
- Have clean lighting.
- Have sharp silhouette.
- Avoid occlusion.
- Avoid text unless text should be applied later during texture.
- Avoid multiple objects.
- Avoid collage of multiple views in one image.
- Avoid environmental effects.

Reference image prompt template:

```text
Single centered [object], full object visible, three-quarter front view, plain white background, clean studio lighting, sharp readable silhouette, clear material zones, no extra objects, optimized for Meshy Image to 3D
```

For riggable character:

```text
Single centered full body humanoid character, A-pose, arms slightly away from torso, legs separated, front-facing view, fitted outfit, no cape, no long skirt, no weapon, plain white background, clean studio lighting, sharp silhouette, optimized for Meshy auto-rigging
```

For print:

```text
Single centered printable figurine, full object visible, flat stable base, thick sturdy parts, no floating pieces, no thin fragile details, minimal overhangs, plain white background, clean studio lighting, optimized for Meshy Image to 3D and 3D printing
```

---

## 7. Texture Master Rules

Texture prompts should not try to rebuild the model. They should describe the look of surfaces.

### 7.1 Texture Prompt Formula

```text
[material], [color], [surface detail], [edge wear/damage], [roughness/metalness], [style], [lighting note]
```

### 7.2 Good Texture Prompts

Leather:

```text
Weathered dark brown leather, visible grain, small stitches along seams, worn edges, subtle dust in creases, matte roughness, realistic PBR game texture
```

Metal:

```text
Brushed gunmetal steel, slightly rough surface, worn silver edges, small scratches, dark oil stains in grooves, realistic PBR material
```

Wood:

```text
Hand-painted fantasy wood texture, warm reddish brown tones, visible large wood grain, carved golden ornaments, soft edge highlights, stylized RPG prop texture
```

Stone:

```text
Ancient carved stone texture, grey limestone base, moss in cracks, chipped edges, rough surface, subtle dirt, realistic ruins material
```

Cartoon:

```text
Bright cartoon texture, clean flat colors, soft painted highlights, simple material separation, minimal noise, friendly stylized game look
```

### 7.3 Texture Edit Workflow

Use Texture Edit when changing a specific selected part:

Prompt example:

```text
Change the selected helmet area to polished bronze metal with engraved floral patterns and darker shadows in the grooves
```

Rules:

- Select only the part you want to alter.
- Prompt that part only.
- Use Prompt Influence Strength higher for stronger change, lower to preserve current look.
- Use healing/stamp/paint tools for small defects.
- Save as new model; do not assume it overwrites original.

### 7.4 Face/Character Texture Editing Note

Community workflow suggests doing face edits late, because repeated edits can blur or degrade face detail. Start with body/clothing/material edits, then polish face last.

---

## 8. Prompt Building Algorithms For Another AI

### 8.1 General Prompt Generation Algorithm

When asked for a Meshy prompt:

1. Identify target:
   - Game static prop
   - Game riggable character
   - Game creature
   - Web/Three.js asset
   - 3D print model
   - Texture/retexture
   - Image reference for Image to 3D

2. Determine output constraints:
   - Game engine: Unity, Unreal, Godot, Roblox, Three.js
   - Camera: top-down, isometric, third-person, first-person, close-up
   - Rig needed: yes/no
   - Animation needed: yes/no
   - Print tech: FDM/resin
   - Print scale
   - Style: realistic, low-poly, hand-painted, anime, cartoon, dark fantasy, sci-fi, product, toy, etc.

3. Generate separate prompts:
   - Model/geometry prompt
   - Optional image reference prompt
   - Texture prompt
   - Optional retexture prompt

4. Include settings advice:
   - Text to 3D vs Image to 3D
   - A/T-pose if humanoid rigging
   - Image Enhancement on/off
   - Multi-view if needed
   - Remesh/topology/polycount suggestion
   - Export format

5. Include avoid list specific to target.

### 8.2 If User Says "Game Asset"

Return:

- Recommended workflow.
- Model prompt.
- Texture prompt.
- If character: riggable version.
- Export recommendation.
- Engine integration checklist.

### 8.3 If User Says "3D Print"

Return:

- Print-safe model prompt.
- Optional image reference prompt.
- Slicer/export advice.
- Print risk list.
- Avoid A/T pose unless game rigging is also needed.

### 8.4 If User Says "Both Game And Print"

Do not produce one prompt. Produce two:

- Game/rig prompt.
- 3D print prompt.

Explain that the same concept should usually be generated as separate models.

---

## 9. Production Checklists

### 9.1 Game Static Prop Checklist

- Single object.
- Clear silhouette.
- Low/medium poly target.
- No useless tiny geometry.
- Texture material zones are clear.
- Scale set.
- Origin bottom or center depending engine use.
- Export GLB or FBX.
- Test in engine with lighting.
- Add collider manually or via engine.
- Generate LOD if needed.

### 9.2 Riggable Character Checklist

- Full body visible.
- Humanoid/biped.
- A-pose or T-pose.
- Arms not fused to torso.
- Legs separated.
- Shoulders, elbows, knees, hands, feet visible.
- No cape/long skirt hiding limbs.
- No weapon attached.
- Short hair or hair not blocking shoulders.
- Textured model.
- Face count under rigging limits.
- Export FBX if animated.
- Test deformation in Blender or engine.

### 9.3 3D Print Checklist

- Closed model.
- No holes/gaps.
- No floating parts.
- Flat stable base.
- Thick parts.
- Minimal overhangs.
- No unsupported long thin features.
- Scale set in mm/cm.
- Export STL or 3MF.
- Check slicer preview.
- Repair non-manifold issues if needed.

### 9.4 Texture Checklist

- Prompt describes surface only.
- Materials separated.
- No unwanted baked dramatic shadows unless needed.
- Use PBR for games/realistic render.
- Use image texture only when geometry matches.
- Text/logos applied in texture stage, not mesh stage.

---

## 10. Troubleshooting

Problem: Character fails rigging.

Likely causes:

- Non-humanoid or unclear body.
- Limbs fused or hidden.
- Cape/robe/skirt hides anatomy.
- Untextured model.
- Too many faces.
- Dynamic pose.

Fix:

- Regenerate as full body humanoid A-pose.
- Separate arms and legs in prompt/reference.
- Remove cape/long skirt/weapon.
- Remesh below limit.
- Texture before rigging.

Problem: Model has floating bits.

Likely causes:

- Prompt included smoke, magic, aura, glitter, particles.
- Too many small accessories.

Fix:

- Remove non-physical effects.
- Use "single solid object", "no floating parts".
- Generate simpler version.

Problem: Print fails or slicer shows issues.

Likely causes:

- Thin walls, overhangs, floating parts, non-manifold mesh, unstable base.

Fix:

- Prompt thick printable parts and flat base.
- Use Meshy Print/Add Base.
- Repair in Blender/Meshmixer/3D Builder.
- Preview supports in slicer.

Problem: Text/logo becomes engraved geometry.

Fix:

- Remove text before mesh generation.
- Add text/logo during texture stage.

Problem: Game asset too heavy.

Fix:

- Prompt low-poly, mobile game, simple geometry, clean silhouette.
- Use Remesh with lower target polycount or adaptive low poly.
- Export GLB for web or FBX for game engines.

Problem: Style inconsistent across assets.

Fix:

- Use same style phrase every time.
- Use same reference image/style guide.
- Use Image to 3D rather than Text to 3D for consistency.
- Generate variations from one good base prompt.

---

## 11. Ready-To-Use Prompt Packs

### 11.1 Game Prop Pack

Model:

```text
Low-poly stylized wooden crate, readable from top-down camera, chunky square silhouette, thick planks, large metal corner brackets, simple geometry, hand-painted fantasy game asset, clean edges, no floating parts
```

Texture:

```text
Hand-painted worn wood texture, warm brown planks, dark cracks, subtle edge highlights, rusty metal brackets, minimal noise, clean mobile game readability
```

### 11.2 Riggable Character Pack

Image reference:

```text
Single centered full body humanoid adventurer, A-pose, arms slightly away from torso, legs separated, fitted leather outfit, short hair, no cape, no long skirt, no weapon, front-facing view, plain white background, clean studio lighting, sharp silhouette, optimized for 3D auto-rigging
```

Model:

```text
Full body humanoid adventurer character, standard biped proportions, clear separated arms and legs, visible shoulders elbows knees hands and feet, fitted leather outfit, short hair, no cape, no long skirt, no weapon attached, symmetrical body, A-pose, stylized RPG game character, ready for auto-rigging
```

Texture:

```text
Stylized RPG texture, brown leather armor, dark cloth undersuit, worn metal buckles, clear material separation, soft painted highlights, subtle dirt in creases, game-ready surface
```

### 11.3 3D Print Figurine Pack

Image reference:

```text
Single centered cute dragon figurine, full body visible, flat circular base, thick legs and tail connected to body, short sturdy wings, chunky horns, plain white background, clean studio lighting, no thin fragile details, no floating parts, optimized for 3D printing
```

Model:

```text
Single solid chibi dragon figurine, flat stable circular base, thick legs and tail connected to the body, short sturdy wings attached to the back, chunky horns, no paper-thin details, no floating parts, minimal overhangs, clean silhouette readable at small scale, 3D printable toy sculpture
```

### 11.4 Same Concept: Game + Print

Game:

```text
Full body humanoid knight enemy, standard biped proportions, separated arms and legs, visible shoulders elbows knees hands and feet, fitted plate armor, no cape, no weapon attached, symmetrical body, A-pose, stylized low-poly RPG enemy, clean silhouette, ready for auto-rigging
```

Print:

```text
Single solid knight figurine, heroic standing pose on round flat base, thick sword attached to hand, shield attached close to body, chunky armor shapes, sturdy helmet crest, minimal overhangs, no floating parts, clean silhouette, 3D printable tabletop miniature
```

---

## 12. Community Research Signals

These are anecdotal patterns from Reddit/community posts. Use as practical hints, not official guarantees.

1. Props and environment pieces are often more reliable than complex characters.
   - Barrels, crates, weapons, potions, furniture, rocks, trees, walls, and simple props tend to be good candidates.

2. Characters and creatures are more hit-or-miss.
   - They may need Blender cleanup, retopology, UV fixes, weight painting, or manual rigging.

3. Do not chase perfection forever.
   - A practical workflow is to generate a few variations, pick the closest 70-80 percent result, then polish manually.

4. Low-poly/mobile prompts help.
   - Repeated terms like "low-poly", "mobile game", "simple geometry", and "clean silhouette" reportedly help keep assets usable.

5. 3D print success varies by category.
   - Hard-surface props, buildings, tabletop props, and simple objects tend to print more easily than organic characters.

6. For print, image-first workflow can help.
   - Some users report best print results from creating a clean image with print-safe language, then using that image as the Image to 3D source.

7. Game production still needs engine/Blender work.
   - Meshy can accelerate asset creation, but real projects still need cleanup, scale/origin checks, colliders, material checks, performance testing, and sometimes rig/weight fixes.

8. Consistent style comes from consistent prompts and reference images.
   - Use repeated style tags and shared reference images across an asset set.

---

## 13. Source Index

Official Meshy Help Center:

- Text to 3D: https://help.meshy.ai/en/articles/9996858-how-to-use-the-text-to-3d-feature
- Image to 3D: https://help.meshy.ai/en/articles/9996860-how-to-use-the-image-to-3d-feature
- Best Practices for Text Prompt: https://help.meshy.ai/en/articles/11972484-best-practices-for-creating-a-text-prompt
- AI Prompt Helper: https://help.meshy.ai/en/articles/11934119-ai-prompt-helper
- Text to Image Feature: https://help.meshy.ai/en/articles/13696156-how-to-use-the-text-to-image-feature
- Texture Feature: https://help.meshy.ai/en/articles/12143359-how-to-use-the-texture-feature
- Text/Image Texture Revamp: https://help.meshy.ai/en/articles/12127474-revamping-model-texture-with-text-prompt-or-image-upload
- Texture Edit: https://help.meshy.ai/en/articles/11936711-how-to-use-texture-edit
- Multi-view: https://help.meshy.ai/en/articles/12634481-how-to-use-multi-view
- Image Enhancement: https://help.meshy.ai/en/articles/13880941-what-does-the-image-enhancement-toggle-do
- Prevent Text Engraving: https://help.meshy.ai/en/articles/14234196-how-to-prevent-text-from-being-engraved-into-your-3d-model-geometry
- A/T Pose and Custom Pose: https://help.meshy.ai/en/articles/10255659-how-do-i-create-an-a-t-pose-or-custom-posed-model
- 3D Printing with Meshy: https://help.meshy.ai/en/articles/11796238-how-to-3d-print-with-meshy
- File Format Guide: https://help.meshy.ai/en/articles/13456840-choosing-the-right-3d-file-format-to-download-your-meshy-models-in
- Unity/Unreal Integration: https://help.meshy.ai/en/articles/11973241-integrating-meshy-assets-into-unity-unreal-engine
- Resize/Reposition: https://help.meshy.ai/en/articles/10523176-resizing-and-repositioning-models-in-meshy
- Quad Mesh Download: https://help.meshy.ai/en/articles/9992029-how-to-download-a-quad-mesh-model

Official Meshy Docs/API:

- Text to 3D API: https://docs.meshy.ai/en/api/text-to-3d
- Image to 3D API: https://docs.meshy.ai/en/api/image-to-3d
- Remesh API: https://docs.meshy.ai/en/api/remesh
- Rigging API: https://docs.meshy.ai/en/api/rigging
- Animation API: https://docs.meshy.ai/en/api/animation

Meshy Blog:

- Meshy 5 Text to 3D Prompt Guide: https://www.meshy.ai/blog/meshy-5-text-to-3d
- Beginner Prompt Guide: https://www.meshy.ai/blog/how-to-write-better-prompts-for-meshy-a-guide-for-beginners
- 50+ Meshy Keywords: https://www.meshy.ai/blog/50%2B-meshy-keywords-to-create-amazing-3d-models
- 10+ Game Asset Prompts: https://www.meshy.ai/blog/10-incredible-meshy-prompts-you-should-try-3d-game-assets
- Sci-fi Character Prompts: https://www.meshy.ai/blog/10-amazing-meshy-prompts-you-should-try-3d-sci-fi-characters
- Game Asset Workflow: https://www.meshy.ai/blog/3d-game-assets-with-meshy

Community / Reddit anecdotal references:

- AI generated 3D assets in game, honest take: https://www.reddit.com/r/meshyai/comments/1sjig1n/using_ai_generated_3d_assets_in_my_game_3_months/
- 3D print success rate discussion: https://www.reddit.com/r/meshyai/comments/1rgbeq7/whats_your_actual_print_success_rate_with_meshy/
- Mobile game prototype using Meshy: https://www.reddit.com/r/meshyai/comments/1rx9z2b/made_all_the_3d_assets_for_my_mobile_game/
- Three.js browser game using Meshy: https://www.reddit.com/r/meshyai/comments/1rix9hj/i_built_a_3d_browser_game_in_a_few_hours_using/
- Meshy workflow turning imagination into 3D art: https://www.reddit.com/r/meshyai/comments/1n9ij6t/workflow_turn_imagination_into_3d_art/
- AI-assisted ARPG workflow with Meshy/Godot: https://www.reddit.com/r/aigamedev/comments/1s72nx6/first_room_combat_ready_for_my_100_aideveloped/

---

## 14. Final Operating Rule

When generating Meshy prompts, always optimize for the final use case:

- Game static prop: clean silhouette, simple geometry, material separation, low/medium poly, engine export.
- Riggable game character: full-body humanoid, A/T pose, separated limbs, visible joints, no cape/skirt/weapon attached, textured, under rigging face limit.
- 3D print model: single solid object, flat stable base, thick printable parts, no floating details, minimal overhangs, export STL/3MF.
- Image to 3D: clean reference image is the prompt.
- Texture: surface only, not geometry.

Never use one universal prompt for both game rigging and 3D printing. Generate two purpose-built prompts from the same concept.
