# Meshy Prompt Studio

Meshy Prompt Studio is a Codex plugin that bundles the `write-meshy-prompts` skill for creating production-ready Meshy prompts and workflow guidance.

Use it for:

- Text to 3D model prompts
- Image to 3D reference prompts
- Texture and retexture prompts
- Game-ready static props
- Riggable humanoid characters
- 3D printable models
- Export and production handoff guidance
- Troubleshooting Meshy generation results

## Install

The plugin manifest lives at:

```text
plugins/meshy-prompt-studio/.codex-plugin/plugin.json
```

The repository marketplace entry lives at:

```text
.agents/plugins/marketplace.json
```

Codex plugin tooling can install this plugin from the repository marketplace entry. The plugin exposes the bundled `write-meshy-prompts` skill after installation.

## Usage

```text
Use $write-meshy-prompts to create a Meshy prompt pack for a riggable game character.
```

```text
Use $write-meshy-prompts to write Image to 3D and texture prompts for this prop.
```

```text
Use $write-meshy-prompts to turn this concept into separate game and 3D print prompts.
```

## Package Contents

```text
.codex-plugin/plugin.json
skills/write-meshy-prompts/
LICENSE.txt
README.md
```

## License

MIT License. See [LICENSE.txt](LICENSE.txt).
