from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from system.editing.asr import request_doubao_asr


ROOT = Path(__file__).resolve().parents[2]
EDITCTL = ROOT / "system/scripts/editctl.py"


class EpisodeCreationTests(unittest.TestCase):
    def write_executable(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    def test_failed_creation_is_retryable_and_moves_staging_to_trash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tools = root / "bin"
            tools.mkdir()
            self.write_executable(
                tools / "hyperframes",
                "#!/bin/sh\n"
                "if [ \"$1\" = \"init\" ]; then\n"
                "  mkdir -p \"$2\"\n"
                "  printf '{\"scripts\":{}}\\n' > \"$2/package.json\"\n"
                "  exit 0\n"
                "fi\n"
                "exit 1\n",
            )
            self.write_executable(tools / "npm", "#!/bin/sh\nexit 9\n")
            episodes = root / "episodes"
            trash = root / "Trash"
            environment = dict(os.environ)
            environment["PATH"] = f"{tools}:{environment['PATH']}"
            environment["EDITING_TRASH_ROOT"] = str(trash)
            command = [
                sys.executable,
                str(EDITCTL),
                "new",
                "retryable",
                "--root",
                str(episodes),
                "--title",
                "Retryable",
            ]

            failed = subprocess.run(
                command, text=True, capture_output=True, check=False, env=environment
            )
            self.assertEqual(failed.returncode, 1)
            self.assertFalse((episodes / "retryable").exists())
            self.assertEqual(len(list(trash.iterdir())), 1)

            self.write_executable(tools / "npm", "#!/bin/sh\nexit 0\n")
            retried = subprocess.run(
                command, text=True, capture_output=True, check=False, env=environment
            )
            self.assertEqual(retried.returncode, 0, retried.stderr)
            self.assertTrue((episodes / "retryable/episode.json").is_file())

    def test_episode_id_cannot_escape_destination_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(EDITCTL),
                    "new",
                    "../escape",
                    "--root",
                    temporary,
                    "--title",
                    "Escape",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("one directory name", completed.stderr)


class SkillInstallerTests(unittest.TestCase):
    def test_install_and_check_survive_a_symlinked_repository_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_repo = root / "real-repo"
            script = real_repo / "system/scripts/install-local-skills.sh"
            script.parent.mkdir(parents=True)
            shutil.copy2(ROOT / "system/scripts/install-local-skills.sh", script)
            for skill in (
                "hyperframe-video-editor",
                "hyperframe-sequence-worker",
                "auto-cover-imagegen",
                "hyperframe-cinematic-templates",
                "hyperframe-editorial-explainer",
            ):
                (real_repo / "skills" / skill).mkdir(parents=True)

            linked_repo = root / "linked-repo"
            linked_repo.symlink_to(real_repo, target_is_directory=True)
            linked_script = linked_repo / "system/scripts/install-local-skills.sh"
            environment = dict(os.environ)
            environment["CODEX_HOME"] = str(root / "codex-home")

            installed = subprocess.run(
                [str(linked_script)],
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )
            self.assertEqual(installed.returncode, 0, installed.stderr)
            checked = subprocess.run(
                [str(linked_script), "--check"],
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)


class CaptionStyleContractTests(unittest.TestCase):
    def make_episode(self, temporary: str, css: str) -> Path:
        episode = Path(temporary) / "episode"
        episode.mkdir()
        manifest = json.loads((ROOT / "config/episode.template.json").read_text(encoding="utf-8"))
        manifest.update({"id": "caption-contract", "title": "Caption Contract"})
        (episode / "episode.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        shutil.copy2(ROOT / "config/editorial-defaults.json", episode / "editorial-defaults.snapshot.json")
        (episode / "styles.css").write_text(css, encoding="utf-8")
        (episode / "index.html").write_text(
            '<div id="captions"><section class="clip body-caption">'
            '<div class="caption-cn">中文</div><div class="caption-en">English</div>'
            "</section></div>\n",
            encoding="utf-8",
        )
        return episode

    def run_style_check(self, episode: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(EDITCTL), "style-check", str(episode)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_canonical_caption_style_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            css = (ROOT / "system/templates/hyperframe-episode/styles.css").read_text(encoding="utf-8")
            completed = self.run_style_check(self.make_episode(temporary, css))
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(json.loads(completed.stdout)["ok"])

    def test_black_caption_box_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            css = ".body-caption { background: rgba(0, 0, 0, 0.8); }\n"
            completed = self.run_style_check(self.make_episode(temporary, css))
            self.assertEqual(completed.returncode, 1)
            report = json.loads(completed.stdout)
            self.assertFalse(report["ok"])
            self.assertTrue(any("background" in issue for issue in report["issues"]))

    def test_decorative_vertical_side_rail_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            css = (
                (ROOT / "system/templates/hyperframe-episode/styles.css").read_text(encoding="utf-8")
                + "\n.callout { border-left: 5px solid #ff4d57; }\n"
            )
            completed = self.run_style_check(self.make_episode(temporary, css))
            self.assertEqual(completed.returncode, 1)
            report = json.loads(completed.stdout)
            self.assertFalse(report["ok"])
            self.assertTrue(any("vertical side rail" in issue for issue in report["issues"]))

    def test_thin_structural_border_is_not_misclassified_as_a_side_rail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            css = (
                (ROOT / "system/templates/hyperframe-episode/styles.css").read_text(encoding="utf-8")
                + "\n.table-cell { border-left: 1px solid rgba(255,255,255,.12); }\n"
            )
            completed = self.run_style_check(self.make_episode(temporary, css))
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_nested_composition_styles_are_scanned_for_decorative_rails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(
                temporary,
                (ROOT / "system/templates/hyperframe-episode/styles.css").read_text(encoding="utf-8"),
            )
            nested = episode / "compositions" / "hook" / "styles.css"
            nested.parent.mkdir(parents=True)
            nested.write_text(".hook-callout { border-right: 6px solid #ff4d57; }\n", encoding="utf-8")
            completed = self.run_style_check(episode)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("compositions/hook/styles.css", completed.stdout)


class SequenceV3Tests(unittest.TestCase):
    def make_episode(self, temporary: str) -> Path:
        episode = Path(temporary) / "episode"
        (episode / "work").mkdir(parents=True)
        (episode / "scripts").mkdir(parents=True)
        manifest = json.loads((ROOT / "config/episode.template.json").read_text(encoding="utf-8"))
        manifest.update({"id": "parallel-test", "title": "Parallel Test"})
        (episode / "episode.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        brief = json.loads((ROOT / "config/creative-brief.template.json").read_text(encoding="utf-8"))
        brief.update(
            {
                "episodeId": "parallel-test",
                "audiencePromise": "看懂并行剪辑",
                "visualThesis": "同一导演判断，多段同时实现",
                "opening": {
                    "firstFrame": "人物带问题入画",
                    "progression": "由近到远建立空间",
                    "handoff": "交接到真实证据",
                },
                "visualMainline": {
                    "motif": "人物与证据的递进交接",
                    "evolution": "提问到证据再到结论",
                },
                "palette": {
                    "ground": "#101114",
                    "content": "#f4f2ea",
                    "structure": "#727982",
                    "semanticAccent": "#ffd400",
                },
                "typography": {
                    "displayHierarchy": "一大一小，关键词放大",
                    "bodyCaptions": "locked-to-editorial-defaults",
                },
                "sound": {
                    "dialoguePriority": True,
                    "direction": "只在可见动作上使用成熟音效",
                },
            }
        )
        (episode / "work/creative-brief.json").write_text(
            json.dumps(brief, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        plan = {
            "schemaVersion": 1,
            "episodeId": "parallel-test",
            "sourceClock": "retimed-aroll",
            "sequences": [
                {
                    "id": "S01",
                    "start": 0,
                    "end": 4,
                    "transcript": "第一个段落",
                    "audienceTask": "建立问题",
                    "primaryVisualRole": "presenter",
                    "design": {
                        "entryState": "人物全景",
                        "visibleAction": "镜头推近",
                        "landedComposition": "人物中景",
                        "exitState": "人物中景保持"
                    }
                },
                {
                    "id": "S02",
                    "start": 4,
                    "end": 9,
                    "transcript": "第二个段落",
                    "audienceTask": "给出证据",
                    "primaryVisualRole": "real-evidence",
                    "design": {
                        "entryState": "人物中景保持",
                        "visibleAction": "证据接过画面",
                        "landedComposition": "证据全屏",
                        "exitState": "证据缩回右上角"
                    },
                    "sourceMedia": [
                        {
                            "path": "source/proof.png",
                            "relationship": "direct-evidence"
                        }
                    ],
                    "capabilities": [
                        {"techniqueId": "technique.evidence.symmetric-tableau"}
                    ]
                }
            ]
        }
        (episode / "work/sequence-plan.json").write_text(
            json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (episode / "BRIEF.md").write_text("# Brief\n\n让证据接管空洞表述。\n", encoding="utf-8")
        (episode / "SCRIPT.md").write_text("# Script\n\n第一个段落。第二个段落。\n", encoding="utf-8")
        (episode / "SOURCES.md").write_text("# Sources\n\nproof.png 是自有真实素材。\n", encoding="utf-8")
        (episode / "DESIGN.md").write_text("# Design\n\n人物始终是视觉因果中心。\n", encoding="utf-8")
        (episode / "MOTION-STORYBOARD.md").write_text("# Storyboard\n", encoding="utf-8")
        proof = episode / "source" / "proof.png"
        proof.parent.mkdir(parents=True)
        proof.write_bytes(b"real-image-proof")
        shutil.copy2(
            ROOT / "system/templates/hyperframe-episode/index.template.html",
            episode / "index.template.txt",
        )
        shutil.copy2(
            ROOT / "system/templates/hyperframe-episode/build_index.mjs",
            episode / "scripts/build_index.mjs",
        )
        return episode

    def run_editctl(self, *arguments: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [sys.executable, str(EDITCTL), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, expected, completed.stderr)
        return completed

    def write_worker_output(self, episode: Path, sequence_id: str) -> None:
        directory = episode / "sequences" / sequence_id
        task = json.loads((directory / "TASK.json").read_text(encoding="utf-8"))
        (directory / "scene.html").write_text(
            f'<section id="{sequence_id}-root" data-sequence="{sequence_id}"></section>\n',
            encoding="utf-8",
        )
        (directory / "styles.css").write_text(
            f"#{sequence_id}-root {{ position: absolute; }}\n",
            encoding="utf-8",
        )
        (directory / "timeline.js").write_text(
            f'timeline.set("#{sequence_id}-root", {{ opacity: 1 }}, {task["sequence"]["start"]});\n',
            encoding="utf-8",
        )
        output = {
            "schemaVersion": 1,
            "sequenceId": sequence_id,
            "taskFingerprint": task["taskFingerprint"],
            "status": "ready",
            "files": {
                "fragment": "scene.html",
                "styles": "styles.css",
                "timeline": "timeline.js",
                "assets": []
            },
            "landedResult": task["sequence"]["design"]["landedComposition"],
            "boundaryResult": {
                "entryState": task["sequence"]["design"]["entryState"],
                "exitState": task["sequence"]["design"]["exitState"],
            },
            "usedSources": [item["path"] for item in task.get("sourceContract", [])],
            "usedCapabilities": [item["techniqueId"] for item in task.get("capabilityContract", [])],
            "notes": ["已按语义落成"]
        }
        (directory / "sequence.json").write_text(
            json.dumps(output, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_pack_check_and_assemble_parallel_sequences(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            packed = self.run_editctl("pack-sequences", str(episode))
            report = json.loads(packed.stdout)
            self.assertEqual(report["systemVersion"], 3)
            self.assertEqual([item["sequenceId"] for item in report["tasks"]], ["S01", "S02"])

            first_task = json.loads((episode / "sequences/S01/TASK.json").read_text(encoding="utf-8"))
            self.assertIsNone(first_task["neighbors"]["previous"])
            self.assertEqual(first_task["neighbors"]["next"]["boundaryState"], "人物中景保持")

            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            checked = self.run_editctl("check-sequences", str(episode))
            self.assertTrue(json.loads(checked.stdout)["ok"])
            self.run_editctl("assemble-sequences", str(episode))
            assembly = json.loads((episode / "work/assembly-plan.json").read_text(encoding="utf-8"))
            self.assertEqual([item["id"] for item in assembly["sequences"]], ["S01", "S02"])
            self.assertEqual(assembly["systemVersion"], 3)
            self.assertRegex(assembly["creativeBriefSha256"], r"^[a-f0-9]{64}$")
            self.assertRegex(assembly["sequencePlanSha256"], r"^[a-f0-9]{64}$")
            self.assertRegex(
                assembly["sequences"][0]["artifactSha256"]["sequences/S01/scene.html"],
                r"^[a-f0-9]{64}$",
            )
            second = assembly["sequences"][1]
            self.assertEqual(second["landedResult"], "证据全屏")
            self.assertEqual(second["usedSources"], ["source/proof.png"])
            self.assertEqual(
                second["usedCapabilities"],
                ["technique.evidence.symmetric-tableau"],
            )
            self.assertEqual(second["boundaryResult"]["exitState"], "证据缩回右上角")

            if shutil.which("node"):
                (episode / "scripts").mkdir(exist_ok=True)
                shutil.copy2(
                    ROOT / "system/templates/hyperframe-episode/build_index.mjs",
                    episode / "scripts/build_index.mjs",
                )
                shutil.copy2(
                    ROOT / "system/templates/hyperframe-episode/index.template.html",
                    episode / "index.template.txt",
                )
                shutil.copy2(
                    ROOT / "system/templates/hyperframe-episode/styles.css",
                    episode / "styles.css",
                )
                shutil.copy2(
                    ROOT / "config/editorial-defaults.json",
                    episode / "editorial-defaults.snapshot.json",
                )
                (episode / "work/a-roll.json").write_text(
                    json.dumps({"duration": 9}, indent=2) + "\n",
                    encoding="utf-8",
                )
                subprocess.run(
                    ["node", "scripts/build_index.mjs"],
                    cwd=episode,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                html = (episode / "index.html").read_text(encoding="utf-8")
                self.assertIn('id="S01-root"', html)
                self.assertIn('id="S02-root"', html)
                self.assertIn("/* V3 sequence S01 */", html)
                self.assertIn("// V3 sequence S02", html)

    def test_check_reports_each_ready_sequence_when_another_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")

            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            report = json.loads(checked.stdout)
            self.assertEqual(report["ready"], 1)
            self.assertEqual(report["total"], 2)

    def test_changed_sequence_asset_makes_existing_assembly_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            asset = episode / "sequences/S01/assets/proof.txt"
            asset.parent.mkdir(parents=True)
            asset.write_text("first", encoding="utf-8")
            output_path = episode / "sequences/S01/sequence.json"
            output = json.loads(output_path.read_text(encoding="utf-8"))
            output["files"]["assets"] = ["assets/proof.txt"]
            output_path.write_text(
                json.dumps(output, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self.run_editctl("assemble-sequences", str(episode))

            shutil.copy2(
                ROOT / "config/editorial-defaults.json",
                episode / "editorial-defaults.snapshot.json",
            )
            shutil.copy2(
                ROOT / "system/templates/hyperframe-episode/styles.css",
                episode / "styles.css",
            )
            asset.write_text("changed", encoding="utf-8")
            checked = self.run_editctl("style-check", str(episode), expected=1)
            report = json.loads(checked.stdout)
            self.assertTrue(
                any("stale after sequence output changes" in issue for issue in report["issues"])
            )

    def test_changed_task_invalidates_worker_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            plan_path = episode / "work/sequence-plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["sequences"][0]["design"]["visibleAction"] = "镜头快速拉远"
            plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            blocked = self.run_editctl("pack-sequences", str(episode), expected=1)
            self.assertIn("task packet changed", blocked.stderr)
            self.run_editctl("pack-sequences", str(episode), "--force")
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("stale", checked.stdout)

    def test_current_plan_and_task_are_revalidated_without_repacking(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            plan_path = episode / "work/sequence-plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["sequences"][0]["audienceTask"] = "改变后的任务"
            plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("TASK.json is stale", checked.stdout)

            plan["sequences"][0]["audienceTask"] = "建立问题"
            plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            task_path = episode / "sequences/S01/TASK.json"
            task = json.loads(task_path.read_text(encoding="utf-8"))
            task["sequence"]["transcript"] = "被篡改但未重算指纹"
            task_path.write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("TASK.json is stale", checked.stdout)

    def test_worker_css_and_timeline_must_stay_in_sequence_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            (episode / "sequences/S01/styles.css").write_text(
                "#S01-root { position: absolute; }\nbody { display: none; }\n",
                encoding="utf-8",
            )
            (episode / "sequences/S01/timeline.js").write_text(
                'timeline.set("#caption-1", { opacity: 0 }, 0);\nthis is invalid js\n',
                encoding="utf-8",
            )
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("unscoped CSS selector", checked.stdout)
            self.assertIn("outside its sequence", checked.stdout)
            self.assertIn("JavaScript is invalid", checked.stdout)

    def test_sequence_namespace_must_be_the_selector_subject(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            (episode / "sequences/S01/styles.css").write_text(
                "body:has(#S01-root) { overflow: hidden; }\n"
                "#S01-root + body { display: none; }\n",
                encoding="utf-8",
            )
            (episode / "sequences/S01/timeline.js").write_text(
                'timeline.set("body:has(#S01-root)", { opacity: 0 }, 0);\n'
                'timeline.set("#S01-root + body", { opacity: 0 }, 0);\n',
                encoding="utf-8",
            )
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("unscoped CSS selector", checked.stdout)
            self.assertIn("outside its sequence", checked.stdout)

    def test_worker_cannot_clear_timeline_target_body_or_import_css(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            (episode / "sequences/S01/styles.css").write_text(
                '@import url("https://example.invalid/global.css");\n'
                "#S01-root { position: absolute; }\n",
                encoding="utf-8",
            )
            (episode / "sequences/S01/timeline.js").write_text(
                'timeline.clear();\n'
                'timeline["clear"]();\n'
                'const localTimeline = timeline; localTimeline.clear();\n'
                'timeline/* bypass */["clear"]();\n'
                'const wrappedTimeline = (timeline); wrappedTimeline.clear();\n'
                'let assignedTimeline; assignedTimeline = timeline; assignedTimeline.clear();\n'
                'const templateResult = `${timeline.clear()}`;\n'
                'String.raw`${timeline.clear()}`;\n'
                'timeline.to("#S01-root, body", { opacity: 0 }, 0);\n'
                'gsap.set("body", { display: "none" });\n',
                encoding="utf-8",
            )
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("@import", checked.stdout)
            self.assertIn("method 'clear' is not allowed", checked.stdout)
            self.assertIn("may only appear as a direct", checked.stdout)
            self.assertIn("template literals are not allowed", checked.stdout)
            self.assertIn("only direct timeline animation statements", checked.stdout)
            self.assertIn("outside its sequence", checked.stdout)
            self.assertIn("may not call gsap directly", checked.stdout)

    def test_worker_cannot_reference_undeclared_local_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            (episode / "sequences/S01/scene.html").write_text(
                '<section id="S01-root" data-sequence="S01">'
                '<img src="source/proof.png"></section>\n',
                encoding="utf-8",
            )
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("undeclared local asset referenced by worker", checked.stdout)

    def test_worker_cannot_reference_external_or_timeline_injected_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            (episode / "sequences/S01/scene.html").write_text(
                '<section id="S01-root" data-sequence="S01">'
                '<img id="S01-image" src="https://example.invalid/proof.png"></section>\n',
                encoding="utf-8",
            )
            (episode / "sequences/S01/styles.css").write_text(
                '#S01-root { '
                'background-image: url("data:image/png;base64,AAAA"); '
                'mask-image: image-set("https://example.invalid/mask.png" 1x); }\n',
                encoding="utf-8",
            )
            (episode / "sequences/S01/timeline.js").write_text(
                'timeline.set("#S01-image", { attr: { ["src"]: "https://example.invalid/a.png" } }, 0);\n'
                'timeline.set("#S01-image", { attr: { src: `https://example.invalid/b.png` } }, 0);\n'
                'timeline.set("#S01-image", { attr: { src: ["source", "/proof.png"].join("") } }, 0);\n',
                encoding="utf-8",
            )
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("external or embedded resource is not allowed", checked.stdout)
            self.assertIn("dynamic-resource-expression", checked.stdout)
            self.assertIn("undeclared local asset referenced by worker", checked.stdout)

    def test_worker_timeline_arguments_cannot_execute_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            (episode / "sequences/S01/timeline.js").write_text(
                'timeline.set("#S01-root", '
                '(self["doc" + "ument"]["body"].replaceChildren(), { opacity: 1 }), 0);\n',
                encoding="utf-8",
            )
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("only strings, numbers, booleans, arrays, and objects", checked.stdout)

    def test_worker_timeline_rejects_dynamically_computed_resource_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            (episode / "sequences/S01/timeline.js").write_text(
                'timeline.set("#S01-root", { attr: { '
                '["s" + "rc"]: ["da", "ta:image/png;base64,AAAA"].join("") } }, 0);\n',
                encoding="utf-8",
            )
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("object keys must be direct identifiers or quoted strings", checked.stdout)

    def test_worker_timeline_rejects_escape_obfuscated_resources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            (episode / "sequences/S01/timeline.js").write_text(
                r'timeline.set("#S01-root", { attr: { "s\x72c": "h\x74tps://example.invalid/a.png" } }, 0);'
                "\n",
                encoding="utf-8",
            )
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("may only escape their quote or backslash", checked.stdout)

    def test_referenced_source_must_be_reported_by_worker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            (episode / "sequences/S02/scene.html").write_text(
                '<section id="S02-root" data-sequence="S02">'
                '<img src="source/proof.png"></section>\n',
                encoding="utf-8",
            )
            output_path = episode / "sequences/S02/sequence.json"
            output = json.loads(output_path.read_text(encoding="utf-8"))
            output["usedSources"] = []
            output_path.write_text(
                json.dumps(output, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("source is referenced but missing from usedSources", checked.stdout)

    def test_shared_context_change_invalidates_task(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            (episode / "MOTION-STORYBOARD.md").write_text(
                "# Storyboard\n\nDirector changed the visual intent.\n",
                encoding="utf-8",
            )
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("TASK.json is stale", checked.stdout)

    def test_design_and_sources_changes_invalidate_task(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            (episode / "DESIGN.md").write_text("# Design\n\n改成新的光影与空间方向。\n", encoding="utf-8")
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("TASK.json is stale", checked.stdout)

    def test_source_and_capability_contracts_are_hashed_into_task(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            task = json.loads((episode / "sequences/S02/TASK.json").read_text(encoding="utf-8"))
            self.assertEqual(task["sourceContract"][0]["path"], "source/proof.png")
            self.assertRegex(task["sourceContract"][0]["sha256"], r"^[a-f0-9]{64}$")
            self.assertEqual(
                task["capabilityContract"][0]["techniqueId"],
                "technique.evidence.symmetric-tableau",
            )
            self.assertTrue(task["capabilityContract"][0]["resolved"])
            linked_files = task["capabilityContract"][0]["assets"][0]["files"]
            implementation = next(item for item in linked_files if item["field"] == "implementation")
            self.assertTrue(implementation["exists"])
            self.assertRegex(implementation["sha256"], r"^[a-f0-9]{64}$")

    def test_pack_rejects_missing_capability_asset_or_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            plan_path = episode / "work/sequence-plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["sequences"][1]["capabilities"][0].update(
                {
                    "assetId": "asset.does-not-exist",
                    "reference": "references/does-not-exist.md",
                }
            )
            plan_path.write_text(
                json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            blocked = self.run_editctl("pack-sequences", str(episode), expected=1)
            self.assertIn("capability asset is not in the asset registry", blocked.stderr)
            self.assertIn("capability reference does not exist", blocked.stderr)

    def test_worker_cannot_claim_undeclared_sources_or_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            output_path = episode / "sequences/S02/sequence.json"
            output = json.loads(output_path.read_text(encoding="utf-8"))
            output["usedSources"].append("source/not-declared.mov")
            output["usedCapabilities"].append("technique.not-declared")
            output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("undeclared source", checked.stdout)
            self.assertIn("undeclared capability", checked.stdout)

    def test_blank_creative_brief_is_rejected_before_packing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            brief_path = episode / "work/creative-brief.json"
            brief = json.loads(brief_path.read_text(encoding="utf-8"))
            brief["visualThesis"] = ""
            brief_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            blocked = self.run_editctl("pack-sequences", str(episode), expected=1)
            self.assertIn("creative brief", blocked.stderr)

    def test_schema_invalid_sequence_entries_report_contract_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            plan_path = episode / "work/sequence-plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["sequences"] = [None, {**plan["sequences"][0], "sourceMedia": ["bad"], "capabilities": ["bad"]}]
            plan_path.write_text(
                json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            blocked = self.run_editctl("pack-sequences", str(episode), expected=1)
            self.assertIn("sequence 0 must be an object", blocked.stderr)
            self.assertNotIn("AttributeError", blocked.stderr)
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("sequence 0 must be an object", checked.stdout)

    def test_pack_reports_non_object_plan_and_existing_task(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            plan_path = episode / "work/sequence-plan.json"
            valid_plan = plan_path.read_text(encoding="utf-8")
            plan_path.write_text("[]\n", encoding="utf-8")
            malformed_plan = self.run_editctl("pack-sequences", str(episode), expected=1)
            self.assertIn("sequence plan", malformed_plan.stderr)
            self.assertNotIn("AttributeError", malformed_plan.stderr)

            plan_path.write_text(valid_plan, encoding="utf-8")
            self.run_editctl("pack-sequences", str(episode))
            (episode / "sequences/S01/TASK.json").write_text("[]\n", encoding="utf-8")
            malformed_task = self.run_editctl("pack-sequences", str(episode), expected=1)
            self.assertIn("existing task packet is invalid", malformed_task.stderr)
            self.assertNotIn("AttributeError", malformed_task.stderr)

    def test_worker_timeline_requires_absolute_position_inside_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            (episode / "sequences/S02/timeline.js").write_text(
                'timeline.to("#S02-root", { opacity: 1 });\n'
                'timeline.set("#S02-root", { opacity: 1 }, 0);\n',
                encoding="utf-8",
            )
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("explicit absolute position", checked.stdout)
            self.assertIn("outside sequence 4.0-9.0", checked.stdout)

            (episode / "sequences/S02/scene.html").write_text(
                '<section id="S02-root" data-sequence="S02">'
                '<div id="S02-readability"></div></section>\n',
                encoding="utf-8",
            )
            (episode / "sequences/S02/timeline.js").write_text(
                'timeline.set("#S02-root", { autoAlpha: 0 }, 0);\n'
                'timeline.set("#S02-readability", { autoAlpha: 1 }, 0);\n'
                'timeline.set("#S02-root", { autoAlpha: 1 }, 4);\n',
                encoding="utf-8",
            )
            initialized = self.run_editctl("check-sequences", str(episode))
            self.assertTrue(json.loads(initialized.stdout)["ok"])

            (episode / "sequences/S02/scene.html").write_text(
                '<section id="S02-root" data-sequence="S02"></section>'
                '<div id="S02-sibling"></div>\n',
                encoding="utf-8",
            )
            (episode / "sequences/S02/timeline.js").write_text(
                'timeline.set("#S02-root", { autoAlpha: 0 }, 0);\n'
                'timeline.set("#S02-sibling", { autoAlpha: 1 }, 0);\n'
                'timeline.set("#S02-root", { autoAlpha: 1 }, 4);\n',
                encoding="utf-8",
            )
            sibling = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("outside sequence 4.0-9.0", sibling.stdout)

            (episode / "sequences/S02/scene.html").write_text(
                '<p id="S02-root"><div id="S02-browser-sibling"></div>\n',
                encoding="utf-8",
            )
            (episode / "sequences/S02/timeline.js").write_text(
                'timeline.set("#S02-root", { autoAlpha: 0 }, 0);\n'
                'timeline.set("#S02-browser-sibling", { autoAlpha: 1 }, 0);\n'
                'timeline.set("#S02-root", { autoAlpha: 1 }, 4);\n',
                encoding="utf-8",
            )
            implicit_sibling = self.run_editctl(
                "check-sequences", str(episode), expected=1
            )
            self.assertIn("stable div or section container", implicit_sibling.stdout)

    def test_malformed_worker_output_reports_contract_issues(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S02")
            task = json.loads(
                (episode / "sequences/S01/TASK.json").read_text(encoding="utf-8")
            )
            (episode / "sequences/S01/sequence.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "sequenceId": "S01",
                        "taskFingerprint": task["taskFingerprint"],
                        "status": "ready",
                        "files": ["scene.html"],
                        "landedResult": "人物中景",
                    }
                ),
                encoding="utf-8",
            )
            checked = self.run_editctl("check-sequences", str(episode), expected=1)
            self.assertIn("files must be object", checked.stdout)

    def test_builder_rejects_assembly_paths_outside_episode(self) -> None:
        if not shutil.which("node"):
            self.skipTest("Node is required")
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            self.run_editctl("assemble-sequences", str(episode))
            assembly_path = episode / "work/assembly-plan.json"
            assembly = json.loads(assembly_path.read_text(encoding="utf-8"))
            assembly["sequences"][0]["files"]["fragment"] = "../outside.html"
            assembly_path.write_text(json.dumps(assembly), encoding="utf-8")
            completed = subprocess.run(
                ["node", "scripts/build_index.mjs"],
                cwd=episode,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("escapes the episode", completed.stderr)

    def test_nonempty_sequence_plan_requires_assembly_before_build(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            checked = self.run_editctl("style-check", str(episode), expected=1)
            self.assertIn("assembly plan missing", checked.stdout)

            if shutil.which("node"):
                completed = subprocess.run(
                    ["node", "scripts/build_index.mjs"],
                    cwd=episode,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("assembly plan missing", completed.stderr)

    def test_builder_rejects_empty_or_stale_assembly(self) -> None:
        if not shutil.which("node"):
            self.skipTest("Node is required")
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            self.run_editctl("assemble-sequences", str(episode))
            assembly_path = episode / "work/assembly-plan.json"
            assembly = json.loads(assembly_path.read_text(encoding="utf-8"))
            assembly["sequences"] = []
            assembly_path.write_text(json.dumps(assembly), encoding="utf-8")
            incomplete = subprocess.run(
                ["node", "scripts/build_index.mjs"],
                cwd=episode,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(incomplete.returncode, 0)
            self.assertIn("coverage is incomplete", incomplete.stderr)

            self.run_editctl("assemble-sequences", str(episode))
            scene_path = episode / "sequences/S01/scene.html"
            scene_path.write_text(
                '<section id="S01-root" data-sequence="S01">tampered</section>\n',
                encoding="utf-8",
            )
            changed_artifact = subprocess.run(
                ["node", "scripts/build_index.mjs"],
                cwd=episode,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(changed_artifact.returncode, 0)
            self.assertIn("artifact changed", changed_artifact.stderr)

            self.run_editctl("assemble-sequences", str(episode))
            brief_path = episode / "work/creative-brief.json"
            brief = json.loads(brief_path.read_text(encoding="utf-8"))
            brief["visualThesis"] = "changed after assembly"
            brief_path.write_text(json.dumps(brief), encoding="utf-8")
            stale = subprocess.run(
                ["node", "scripts/build_index.mjs"],
                cwd=episode,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(stale.returncode, 0)
            self.assertIn("assembly plan is stale", stale.stderr)

    def test_builder_rejects_empty_or_malformed_plan_with_old_assembly(self) -> None:
        if not shutil.which("node"):
            self.skipTest("Node is required")
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            self.run_editctl("assemble-sequences", str(episode))
            plan_path = episode / "work/sequence-plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["sequences"] = []
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            stale = subprocess.run(
                ["node", "scripts/build_index.mjs"],
                cwd=episode,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(stale.returncode, 0)
            self.assertIn("stale sequence artifacts", stale.stderr)

            plan_path.write_text("[]\n", encoding="utf-8")
            malformed = subprocess.run(
                ["node", "scripts/build_index.mjs"],
                cwd=episode,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(malformed.returncode, 0)
            self.assertIn("sequence plan is malformed", malformed.stderr)

    def test_builder_rejects_symlink_to_file_outside_episode(self) -> None:
        if not shutil.which("node"):
            self.skipTest("Node is required")
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            outside = Path(temporary) / "outside.html"
            outside.write_text("<div>outside</div>", encoding="utf-8")
            (episode / "leak.html").symlink_to(outside)
            self.run_editctl("pack-sequences", str(episode))
            self.write_worker_output(episode, "S01")
            self.write_worker_output(episode, "S02")
            self.run_editctl("assemble-sequences", str(episode))
            assembly_path = episode / "work/assembly-plan.json"
            assembly = json.loads(assembly_path.read_text(encoding="utf-8"))
            assembly["sequences"][0]["files"]["fragment"] = "leak.html"
            assembly_path.write_text(json.dumps(assembly), encoding="utf-8")
            completed = subprocess.run(
                ["node", "scripts/build_index.mjs"],
                cwd=episode,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("resolves outside the episode", completed.stderr)

    def test_upgrade_v3_migrates_existing_runtime_with_backups(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            old_template = """<!doctype html><html><head></head><body>
<!-- AI-DIRECTED-SCENES -->{{CAPTIONS}}
<script>// AI-DIRECTED-TIMELINE\nwindow.__timelines = {};</script>
</body></html>\n"""
            (episode / "index.template.txt").write_text(old_template, encoding="utf-8")
            (episode / "scripts/build_index.mjs").write_text("// old builder\n", encoding="utf-8")

            upgraded = self.run_editctl("upgrade-v3", str(episode))
            self.assertTrue(json.loads(upgraded.stdout)["ok"])
            template = (episode / "index.template.txt").read_text(encoding="utf-8")
            for placeholder in ("SEQUENCE_STYLES", "SEQUENCE_SCENES", "SEQUENCE_TIMELINE"):
                self.assertIn(placeholder, template)
            self.assertTrue(
                (episode / "work/migrations/v3/index.template.txt").is_file()
            )
            self.assertTrue(
                (episode / "work/migrations/v3/scripts/build_index.mjs").is_file()
            )
            agents = (episode / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("hyperframe-video-editor", agents)
            self.assertNotIn("/hyperframes`", agents)

    def test_repeated_upgrade_preserves_each_changed_agents_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            self.run_editctl("upgrade-v3", str(episode))
            agents_path = episode / "AGENTS.md"
            first_custom = "# custom episode route one\n"
            second_custom = "# custom episode route two\n"
            agents_path.write_text(first_custom, encoding="utf-8")
            self.run_editctl("upgrade-v3", str(episode))
            agents_path.write_text(second_custom, encoding="utf-8")
            self.run_editctl("upgrade-v3", str(episode))
            backups = list((episode / "work/migrations/v3").glob("AGENTS*.md"))
            contents = {path.read_text(encoding="utf-8") for path in backups}
            self.assertIn(first_custom, contents)
            self.assertIn(second_custom, contents)

    def test_preview_verify_defaults_to_preview_delivery_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            checked = self.run_editctl(
                "verify", str(episode), "--quality", "preview", expected=1
            )
            self.assertIn("deliverables/preview.mp4", checked.stderr)
            self.assertNotIn("deliverables/master.mp4", checked.stderr)

    def test_custom_sequence_root_is_reflected_in_task_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = self.make_episode(temporary)
            manifest_path = episode / "episode.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["paths"]["sequenceRoot"] = "work/custom-sequences"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self.run_editctl("pack-sequences", str(episode))
            task = json.loads(
                (episode / "work/custom-sequences/S01/TASK.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                task["outputContract"]["exclusiveWriteRoot"],
                "work/custom-sequences/S01",
            )


class DoctorReadinessTests(unittest.TestCase):
    def test_full_edit_mode_reports_missing_asr_as_degraded(self) -> None:
        environment = dict(os.environ)
        environment.pop("DOUBAO_APP_KEY", None)
        environment.pop("DOUBAO_ACCESS_KEY", None)
        completed = subprocess.run(
            [sys.executable, str(EDITCTL), "doctor", "--mode", "full-edit"],
            text=True,
            capture_output=True,
            check=False,
            env=environment,
        )
        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        self.assertEqual(report["readiness"]["fullEdit"]["status"], "degraded")
        self.assertIn("doubao-asr", report["readiness"]["fullEdit"]["missing"])
        remediation = {item["issue"]: item for item in report["remediation"]}
        self.assertIn("doubao-asr", remediation)
        self.assertTrue(remediation["doubao-asr"]["secret"])
        self.assertIn("DOUBAO_APP_KEY", remediation["doubao-asr"]["action"])

    def test_pending_remote_references_are_warnings_not_full_edit_blockers(self) -> None:
        environment = dict(os.environ)
        environment["DOUBAO_APP_KEY"] = "configured-for-readiness-test"
        environment["DOUBAO_ACCESS_KEY"] = "configured-for-readiness-test"
        completed = subprocess.run(
            [sys.executable, str(EDITCTL), "doctor", "--mode", "full-edit"],
            text=True,
            capture_output=True,
            check=False,
            env=environment,
        )
        report = json.loads(completed.stdout)
        full_edit = report["readiness"]["fullEdit"]
        self.assertFalse(any(item.startswith("remote-reference-assets:") for item in full_edit["missing"]))
        self.assertIn("doubao-asr-unverified", full_edit["missing"])
        self.assertEqual(report["optional"]["doubaoAsr"]["status"], "configured-unverified")
        pending = report["optional"]["remoteReferences"]["pending"]
        if pending:
            self.assertIn(f"remote-reference-assets:{len(pending)}", full_edit["warnings"])


class DoubaoAsrTransportTests(unittest.TestCase):
    class FakeResponse:
        def __init__(self, headers: dict[str, str], body: bytes) -> None:
            self.headers = headers
            self.body = body

        def __enter__(self) -> "DoubaoAsrTransportTests.FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return self.body

    def test_http_success_with_provider_error_is_rejected(self) -> None:
        response = self.FakeResponse(
            {
                "X-Api-Status-Code": "45000000",
                "X-Api-Message": "invalid credentials",
                "X-Tt-Logid": "provider-error-log",
            },
            b'{"result": {}}',
        )
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "probe.mp3"
            destination = Path(temporary) / "probe.json"
            source.write_bytes(b"audio")
            with mock.patch("system.editing.asr.urllib.request.urlopen", return_value=response):
                with self.assertRaisesRegex(RuntimeError, "status=45000000"):
                    request_doubao_asr(source, destination, "app", "access")
            self.assertFalse(destination.exists())

    def test_official_provider_success_code_writes_transcript(self) -> None:
        response = self.FakeResponse(
            {
                "X-Api-Status-Code": "20000000",
                "X-Api-Message": "OK",
                "X-Tt-Logid": "provider-success-log",
            },
            b'{"result": {"text": "ok", "utterances": []}}',
        )
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "probe.mp3"
            destination = Path(temporary) / "probe.json"
            source.write_bytes(b"audio")
            with mock.patch("system.editing.asr.urllib.request.urlopen", return_value=response):
                request_doubao_asr(source, destination, "app", "access")
            report = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(report["text"], "ok")
            self.assertEqual(report["request"]["statusCode"], "20000000")
            self.assertEqual(report["request"]["logId"], "provider-success-log")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg is required")
class EditCtlIntegrationTests(unittest.TestCase):
    def test_inspect_includes_still_images(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Path(temporary) / "episode"
            source_dir = episode / "source"
            source_dir.mkdir(parents=True)
            still = source_dir / "evidence.png"
            subprocess.run(
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "color=c=0xf0e8dc:s=64x48",
                    "-frames:v", "1", str(still),
                ],
                check=True,
            )
            manifest = json.loads((ROOT / "config/episode.template.json").read_text(encoding="utf-8"))
            manifest.update({"id": "image-inventory", "title": "Image Inventory"})
            (episode / "episode.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self.run_editctl("inspect", str(episode))
            inventory = json.loads(
                (episode / manifest["paths"]["inventory"]).read_text(encoding="utf-8")
            )
            self.assertEqual(len(inventory["items"]), 1)
            self.assertEqual(inventory["items"][0]["mediaKind"], "image")
            self.assertEqual(inventory["items"][0]["video"]["width"], 64)
            self.assertRegex(inventory["items"][0]["sha256"], r"^[a-f0-9]{64}$")

    def test_inspect_build_and_verify_aroll(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Path(temporary) / "episode"
            source_dir = episode / "source"
            source_dir.mkdir(parents=True)
            source = source_dir / "take.mov"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=0x224466:s=320x180:r=30:d=2",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:sample_rate=48000:duration=2",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-shortest",
                    str(source),
                ],
                check=True,
            )
            manifest = json.loads((ROOT / "config/episode.template.json").read_text(encoding="utf-8"))
            manifest.update({"id": "integration", "title": "Integration", "profile": "general"})
            manifest["deliveryOverrides"] = {"width": 320, "height": 180, "fps": 30}
            (episode / "episode.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            self.run_editctl("inspect", str(episode))
            inventory_path = episode / manifest["paths"]["inventory"]
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            self.assertEqual(len(inventory["items"]), 1)
            cut_plan_path = episode / manifest["paths"]["cutPlan"]
            cut_plan_path.parent.mkdir(parents=True, exist_ok=True)
            cut_plan_path.write_text(
                json.dumps(
                    {
                        "rate": 1.1,
                        "clips": [
                            {
                                "sourceId": inventory["items"][0]["id"],
                                "sourceStart": 0.2,
                                "sourceEnd": 1.8,
                            }
                        ],
                        "tailHoldSeconds": 0.1,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            self.run_editctl("build-aroll", str(episode))
            output = episode / manifest["paths"]["aRoll"]
            self.assertTrue(output.is_file())
            verified = self.run_editctl("verify", str(episode), "--file", str(output))
            verification = json.loads(verified.stdout)
            self.assertTrue(verification["ok"])
            self.assertEqual(verification["media"]["video"]["colorSpace"], "bt709")
            self.assertIn("integratedLufs", verification["loudness"])
            self.assertLessEqual(verification["loudness"]["truePeakDbtp"], -0.8)

            metadata_path = episode / "work/a-roll.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["duration"] = float(metadata["duration"]) + 5
            metadata_path.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            truncated = subprocess.run(
                [sys.executable, str(EDITCTL), "verify", str(episode), "--file", str(output)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(truncated.returncode, 1, truncated.stderr)
            truncated_report = json.loads(truncated.stdout)
            self.assertTrue(
                any("duration" in issue for issue in truncated_report["issues"])
            )

    def test_verify_rejects_delivery_with_wrong_loudness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Path(temporary) / "episode"
            episode.mkdir()
            output = episode / "quiet.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=0x224466:s=320x180:r=30:d=2",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:sample_rate=48000:duration=2",
                    "-filter:a",
                    "volume=0.01",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-colorspace",
                    "bt709",
                    "-color_primaries",
                    "bt709",
                    "-color_trc",
                    "bt709",
                    "-c:a",
                    "aac",
                    "-ar",
                    "48000",
                    "-shortest",
                    str(output),
                ],
                check=True,
            )
            manifest = json.loads((ROOT / "config/episode.template.json").read_text(encoding="utf-8"))
            manifest.update({"id": "quiet", "title": "Quiet", "profile": "general"})
            manifest["deliveryOverrides"] = {"width": 320, "height": 180, "fps": 30}
            (episode / "episode.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [sys.executable, str(EDITCTL), "verify", str(episode), "--file", str(output)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertTrue(any("loudness" in issue for issue in report["issues"]))

    def test_verify_rejects_truncated_video_stream_hidden_by_long_audio(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            episode = Path(temporary) / "episode"
            (episode / "work").mkdir(parents=True)
            output = episode / "truncated-video.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=0x224466:s=320x180:r=30:d=1",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:sample_rate=48000:duration=2",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-colorspace",
                    "bt709",
                    "-color_primaries",
                    "bt709",
                    "-color_trc",
                    "bt709",
                    "-c:a",
                    "aac",
                    "-ar",
                    "48000",
                    str(output),
                ],
                check=True,
            )
            manifest = json.loads(
                (ROOT / "config/episode.template.json").read_text(encoding="utf-8")
            )
            manifest.update({"id": "truncated-stream", "title": "Truncated Stream"})
            manifest["deliveryOverrides"] = {"width": 320, "height": 180, "fps": 30}
            (episode / "episode.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (episode / "work/a-roll.json").write_text(
                json.dumps({"duration": 2}, indent=2) + "\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(EDITCTL), "verify", str(episode), "--file", str(output)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertTrue(
                any("video stream duration" in issue for issue in report["issues"]),
                report["issues"],
            )

    def run_editctl(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [sys.executable, str(EDITCTL), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        return completed


if __name__ == "__main__":
    unittest.main()
