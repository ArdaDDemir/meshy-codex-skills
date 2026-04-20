# Meshy Codex Skills

Codex skills for creating production-ready Meshy prompts and workflow guidance for 3D asset generation.

## Skills

### write-meshy-prompts

Create Meshy prompts for:

- Text to 3D
- Image to 3D reference images
- Game-ready static props
- Riggable humanoid characters
- 3D printable models
- Texture and retexture workflows
- Export and production handoff guidance
- Troubleshooting bad Meshy generation results

## Install

Install the skill in Codex with:

```text
$skill-installer install https://github.com/ArdaDDemir/meshy-codex-skills/tree/main/skills/write-meshy-prompts
```

Restart Codex after installing so the new skill is discovered.

## Example Prompts

```text
Use $write-meshy-prompts to create a Meshy prompt pack for a riggable low-poly goblin enemy for Unity.
```

```text
Use $write-meshy-prompts to create separate Meshy prompts for a game-ready treasure chest and a 3D printable version of the same concept.
```

```text
Use $write-meshy-prompts to improve this Meshy prompt for Image to 3D and explain what settings I should use.
```

## Repository Structure

```text
skills/
  write-meshy-prompts/
    SKILL.md
    agents/openai.yaml
    references/meshy-prompt-master-guide.md
    LICENSE.txt
```

## Notes

This project is not affiliated with or endorsed by Meshy. Meshy is a trademark of its respective owner.

The skill includes prompt workflow guidance based on official Meshy documentation, Meshy blog posts, and practical community workflow signals collected in April 2026. Official Meshy documentation should be treated as authoritative for current platform behavior.

## License

MIT License. See [LICENSE.txt](LICENSE.txt).
