# Million AI Editor / 百万AI剪辑师

[简体中文](README.md) | [English](README_EN.md)

> **Million AI Editor / Million Editing OS** turns raw talking-head footage into reviewable, editable, delivery-ready videos.

[![License: MIT](https://img.shields.io/badge/License-MIT-111111.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](pyproject.toml)
[![HyperFrames](https://img.shields.io/badge/Render-HyperFrames-7C3AED.svg)](https://hyperframes.ai/)
[![GitHub stars](https://img.shields.io/github/stars/11Yuxuanyang/million-ai-editor?style=flat&color=D8FF00&labelColor=111111)](https://github.com/11Yuxuanyang/million-ai-editor/stargazers)

**Douyin: AI，我俩和一百万**

We made a decision that would disappoint our ancestors: **we open-sourced it.**

Over more than a month, we studied the editing techniques of over 20 creators, encoded our understanding of high-performing short videos into the system, and tested it across more than 10 real productions. Million AI Editor is not a one-click template generator. It is an editing system in which AI first understands the content, then makes directorial decisions, and finally completes an engineering-grade delivery workflow.

The goal is straightforward: give non-editors a workflow that can improve over time, while letting professional creators move their attention away from repetitive work and back to content, judgment, and creation.

## Real Results

The following frames come from an approved production, not a concept demo. To protect raw footage and client information, the repository includes only one authorized short excerpt, low-resolution contact sheets, transferable composition decisions, and example code.

### Playable 20-second case study

[![Play the 20-second case study](episodes/reference/0813-yujun-boss-content-memory/reference/case-demo-preview-6s.gif)](episodes/reference/0813-yujun-boss-content-memory/reference/case-demo-20s-720p60.mp4)

Click the animated preview to play the `720p60` excerpt with sound. It includes talking-head cutting, bilingual captions, real footage, picture-in-picture, and explanatory animation. The full master and raw footage are not included in the public repository.

### Visual density across a complete talking-head video

![Full edit contact sheet](episodes/reference/0813-yujun-boss-content-memory/reference/formal-master-contact.jpg)

One visual storyline runs through the opening, real evidence, explanatory animation, chapter transitions, and ending. The video does not switch to a different template every ten seconds.

### First three seconds: overturn the obvious answer

![Approved opening contact sheet](library/references/reference.opening.boss-content-memory.v1/contact-sheet.jpg)

An extreme close-up eases into a long-tail pull-back. The expected answer recedes into the visual background while the real conclusion expands from behind the presenter. The person remains the subject throughout.

### Real evidence: scattered facts become proof

![Evidence handoff contact sheet](library/references/reference.person-evidence.scatter-to-proof.v1/contact-sheet.jpg)

Real screenshots align with individual spoken claims. The sequence establishes the source first, then completes a visual handoff from “scattered” to “archived” to “retrievable.”

### VOX: generated visuals explain; they do not impersonate evidence

![VOX two-presenter contact sheet](library/references/reference.generated.vox-two-presenter.v1/contact-sheet.jpg)

Generated media may provide metaphor, explanation, and emotion. It must not pose as news footage, a product page, a chat record, or any other form of real evidence.

## What It Can Do

- Understand unordered video clips, still images, screen recordings, scripts, and supplementary media.
- Transcribe Chinese speech and reconcile it with a reference script instead of guessing the subject from extracted frames.
- Produce a cut plan that removes head-down starts, pauses, and stumbles while preserving meaningful ending gestures and applying the configured speed consistently.
- Write a creative brief and complete motion storyboard before implementation, then distribute continuous semantic sequences across parallel workers when useful.
- Combine A-roll, full-screen B-roll, picture-in-picture, subject-isolated typography, VOX, spatial cards, Lottie, and chapter transitions.
- Preserve a fixed bilingual body-caption specification while redesigning opening display typography for each episode.
- Render a continuous low-resolution preview for human review before producing and validating the final master.
- Extract reusable shot, sound, and taste decisions from approved work, while allowing obsolete rules to be removed instead of accumulated forever.
- Produce `4:3` and `3:4` cover directions for the same episode.

## How It Works

```text
Raw footage + reference script
  → media inspection and transcription
  → content understanding + asset relationships
  → cut plan + A-roll
  → creative brief + complete motion storyboard
  → optional parallel sequence implementation
  → master timeline, captions, and audio assembly
  → continuous low-resolution preview
  → one fast independent review + human screening
  → final master and delivery-spec verification
```

AI owns content understanding, asset relationships, storyboarding, and visual-generation decisions. `editctl.py` handles repeatable mechanical work. The directing agent keeps control of pacing, captions, sound, and final assembly so parallel agents do not produce a collection of unrelated fragments.

## Start in Five Minutes

The production environment is currently verified primarily on macOS. You need:

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Node.js and npm
- FFmpeg / ffprobe
- [HyperFrames CLI](https://hyperframes.ai/)
- Codex, or a compatible agent that can read local Skills, operate on files, and run commands

```bash
git clone https://github.com/11Yuxuanyang/million-ai-editor.git
cd million-ai-editor

uv sync --extra dev
npm install -g hyperframes@0.8.12
./system/scripts/install-local-skills.sh

python3 system/scripts/editctl.py doctor --mode runtime
```

If you use Doubao ASR, keep credentials in your local environment or system keychain. Never commit them:

```bash
export DOUBAO_APP_KEY="..."
export DOUBAO_ACCESS_KEY="..."
python3 system/scripts/editctl.py doctor --mode full-edit --verify-asr
```

## Create an Episode

```bash
python3 system/scripts/editctl.py new 0825-topic --title "Episode title" --profile general
```

Put captured media in the new episode's `source/` directory and write the reference script in `SCRIPT.md`. Ask the agent to read the project `AGENTS.md`, the editing Skill, and episode-local facts before producing `work/cut-plan.json` and `MOTION-STORYBOARD.md`.

Common mechanical commands:

```bash
python3 system/scripts/editctl.py inspect episodes/0825-topic
python3 system/scripts/editctl.py transcribe episodes/0825-topic
python3 system/scripts/editctl.py build-aroll episodes/0825-topic

# Complex videos may be split into continuous semantic sequences.
python3 system/scripts/editctl.py pack-sequences episodes/0825-topic
python3 system/scripts/editctl.py check-sequences episodes/0825-topic
python3 system/scripts/editctl.py assemble-sequences episodes/0825-topic

python3 system/scripts/editctl.py style-check episodes/0825-topic
python3 system/scripts/editctl.py render episodes/0825-topic --quality preview
python3 system/scripts/editctl.py render episodes/0825-topic --quality master --approved
python3 system/scripts/editctl.py verify episodes/0825-topic
```

See the [Contributor Guide](docs/CONTRIBUTOR-GUIDE.md) for the complete setup and contribution workflow.

## Project Structure

```text
AGENTS.md                           project-level principles and routing
config/                             stable production settings and episode contracts
docs/EDITORIAL-MOTHER.md            directorial judgment and core taste
references/SHOT-LANGUAGE.md         professional shot vocabulary
skills/hyperframe-video-editor/     primary editing Skill
skills/hyperframe-sequence-worker/  parallel sequence worker
skills/auto-cover-imagegen/         cover Skill
library/                            taste, techniques, and approved references
references/asset-library/           executable recipes and licensed asset index
episodes/reference/                 compact snapshots of successful cases
system/scripts/editctl.py           unified command-line entry point
system/editing/                     media, ASR, process, and diagnostics modules
```

## Design Principles

- **Few rules, more judgment.** Rules provide direction; they do not replace directing.
- **Visuals serve understanding and emotion first.** Motion is neither decoration nor a quota to change the frame every ten seconds.
- **Real media proves.** Generated media explains and must not masquerade as fact.
- **Design the first three seconds independently.** Subject, display typography, camera motion, and necessary sound must form one complete hook.
- **One visual storyline per episode.** Chapters may change focus and scale without turning the video into a slide deck compilation.
- **Quality does not yield to speed.** Parallelism, caching, and agents reduce waiting; they do not remove understanding or review.

## What It Cannot Do Yet

- It is not an unattended “upload footage and instantly get a viral video” button. Strong output still requires a clear message, usable source material, and final human judgment.
- The repository does not ship platform accounts, model keys, client information, commercial fonts, or audio with undocumented redistribution rights.
- Public references demonstrate methods. They do not grant permission to reuse people, brands, chat records, or pixels from those references in unrelated work.
- Different operating systems, capture specifications, and HyperFrames versions may still require adaptation. Reproducible issues and examples are welcome.

## Open Source and Media Licensing

Original code and documentation are released under the [MIT License](LICENSE). Case videos, identifiable people, third-party transitions, Lottie assets, sound effects, and external references remain subject to their own licenses and are not automatically covered by MIT. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Raw footage, client information, chat screenshots, platform credentials, and complete final masters do not enter Git by default. Confirm that you have the right to use and redistribute every asset before publishing it.

## Star History

[![Million AI Editor Star History](docs/assets/star-history.svg)](https://github.com/11Yuxuanyang/million-ai-editor/stargazers)

The chart is regenerated by the repository's own GitHub Action whenever a new Star arrives and once per day. No access token is handed to a third-party chart service.

## Contributing

We want this system to keep growing instead of being frozen by a rulebook that can never change. Contributions are welcome when they provide:

- shot techniques repeatedly retained in real productions;
- sourced, licensed assets with a clear semantic role;
- reproducible transcription, cutting, rendering, or verification problems;
- deletions and refactors that make the workflow simpler and clearer.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening an Issue or Pull Request.

## Follow and Collaborate

Douyin: **AI，我俩和一百万**

For short-video production, AI editing workflows, brand content, or project collaboration, scan the WeChat code below. Add “合作” and a short project description to your request.

<a href="docs/assets/wechat-contact-yang-yuxuan.jpg"><img src="docs/assets/wechat-contact-yang-yuxuan.jpg" alt="Yang Yuxuan WeChat contact for collaboration" width="360"></a>

Put attention back into creation. Million AI Editor is now open source.
