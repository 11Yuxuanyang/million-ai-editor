#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"
TRANSCRIPTS = ROOT / "transcripts"
WORK = ROOT / "work"
RATE = 1.1

ORDER = [
    "IMG_6151 2",
    "IMG_6155 2",
    "IMG_6161 2",
    "IMG_6162 2",
    "IMG_6163 2",
    "IMG_6167 2",
    "IMG_6168 2",
    "IMG_6170 2",
    "IMG_6173 2",
    "IMG_6175 2",
    "IMG_6204 2",
    "IMG_6218 2",
    "IMG_6222 2",
    "IMG_6226 2",
    "IMG_6227 2",
    "IMG_6229 2",
    "IMG_6236 2",
    "IMG_6245 2",
    "IMG_6246 2",
]

CAPTIONS = {
    "IMG_6155 2": [
        ("因为每拍一条视频", "Every time the team shoots a video,"),
        ("团队还是要重新问他", "they have to ask all over again:"),
        ("老板这一期想讲什么", '"What should this episode be about?"'),
    ],
    "IMG_6161 2": [
        ("老板不是没有东西可以讲", "It isn't that the founder has nothing to say."),
        ("他的观点在微信语音里", "His ideas are buried in voice messages."),
    ],
    "IMG_6162 2": [("案例在员工电脑里", "Cases live on employees' computers.")],
    "IMG_6163 2": [("客户问题散落在聊天记录里面", "Customer questions are scattered across chats.")],
    "IMG_6167 2": [
        ("好不容易招了文案和剪辑", "You finally hire writers and editors,"),
        ("但是在每次开工之前", "but before every project starts..."),
    ],
    "IMG_6168 2": [("所有人还是要等老板重新讲一遍", "everyone still waits for the founder to repeat it all.")],
    "IMG_6170 2": [
        ("老板本来想要把内容交出去", "He wanted to hand content production off,"),
        ("但是却多了一项要反复解释的工作", "but gained another job: explaining it again."),
    ],
    "IMG_6173 2": [
        ("问题不是文案写得慢", "The problem isn't slow writing."),
        ("而是公司根本记不住老板", "The company simply can't remember the founder."),
        ("在语君AI我们有一条最简单的原则", "At Yujun AI, we follow one simple rule:"),
        ("任何做两遍以上的工作", "Any task done more than twice"),
        ("都值得被AI化", "deserves to be AI-enabled."),
    ],
    "IMG_6175 2": [(
        "所以我们改造老版内容的第一步不是让AI随便去写文案",
        "Our first step isn't letting AI write anything it wants.",
    )],
    "IMG_6204 2": [
        ("而是把老板过去的语音", "We collect the founder's past voice notes,"),
        ("产品资料客户问题", "product files and customer questions,"),
        ("全部整理成一套可持续更新的企业记忆", "into a living corporate memory."),
    ],
    "IMG_6218 2": [
        ("下一次老板只需要说出一个想法", "Next time, the founder only needs to share one idea."),
        ("系统就能找到老板之前讲过的观点", "The system retrieves past viewpoints,"),
        ("做过的案例和积累的素材", "cases and accumulated materials,"),
        ("形成文案再进入剪辑", "then drafts the script and sends it into editing."),
    ],
    "IMG_6222 2": [
        ("老板只负责两件最重要的事情", "The founder handles only two important things:"),
        ("做判断", "make the judgment"),
        ("和最终确认", "and give final approval."),
    ],
    "IMG_6226 2": [
        ("这样省下来的不只是一条视频的时间", "This saves more than the time for one video."),
        ("每一次表达都会留下来", "Every expression is retained"),
        ("成为下一次企业可以直接使用的资产", "and becomes a reusable company asset."),
    ],
    "IMG_6227 2": [
        ("老板说过两遍的话", "If the founder has said it twice,"),
        ("就不该说第三遍", "he shouldn't start from scratch a third time."),
    ],
    "IMG_6229 2": [
        ("这里是语君AI", "This is Yujun AI."),
        ("接下来我们会一项项改造", "Next, we'll transform these workflows one by one:"),
        ("企业里那些需要不断重复却离不开人的工作", "repetitive work companies still depend on people to do."),
    ],
    "IMG_6236 2": [
        ("如果你也在做老板IP", "If you're building a founder-led content brand,"),
        ("那就把过去三条的视频私信给我们", "DM us three of your previous videos."),
    ],
    "IMG_6245 2": [
        ("我们先帮您判断", "We'll first diagnose"),
        ("缺的是文案素材", "whether you lack scripts or materials,"),
    ],
    "IMG_6246 2": [(
        "还是一套真正能够运转的内容生产流程",
        "or a content production system that actually runs.",
    )],
}


def duration(path: Path) -> float:
    return float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(path),
            ],
            text=True,
        ).strip()
    )


def compact(value: str) -> str:
    return "".join(character for character in value if character.isalnum())


def find_phrase(words, phrase):
    target = compact(phrase).lower()
    tokens = [(index, compact(word["text"]).lower()) for index, word in enumerate(words)]
    tokens = [(index, token) for index, token in tokens if token]
    for start_pos in range(len(tokens)):
        built = ""
        for end_pos in range(start_pos, len(tokens)):
            built += tokens[end_pos][1]
            if built == target:
                return tokens[start_pos][0], tokens[end_pos][0]
            if not target.startswith(built):
                break
    return None


def main():
    timeline = []
    captions = []
    cursor = 0.0
    trim_lines = ["source\tsourceStart\tsourceEnd\toutputStart\toutputDuration\ttext"]

    for index, stem in enumerate(ORDER):
        source = SOURCE / f"{stem}.MOV"
        transcript = json.loads((TRANSCRIPTS / f"{stem}.json").read_text(encoding="utf-8"))
        utterances = transcript["utterances"]
        source_duration = duration(source)
        source_start = max(0.0, utterances[0]["startMs"] / 1000 - 0.08)
        source_end = min(source_duration, utterances[-1]["endMs"] / 1000 + 0.08)
        output_duration = (source_end - source_start) / RATE
        item = {
            "index": index + 1,
            "id": stem,
            "source": str(source),
            "sourceStart": round(source_start, 4),
            "sourceEnd": round(source_end, 4),
            "outputStart": round(cursor, 4),
            "outputDuration": round(output_duration, 4),
            "text": transcript["text"],
        }
        timeline.append(item)
        trim_lines.append(
            f"{stem}\t{source_start:.3f}\t{source_end:.3f}\t{cursor:.3f}\t{output_duration:.3f}\t{transcript['text']}"
        )

        words = [word for utterance in utterances for word in utterance.get("words") or []]
        for chinese, english in CAPTIONS.get(stem, []):
            match = find_phrase(words, chinese)
            if match is None:
                raise RuntimeError(f"caption phrase not found in {stem}: {chinese}")
            first, last = match
            start = cursor + ((words[first]["startMs"] / 1000) - source_start) / RATE
            end = cursor + ((words[last]["endMs"] / 1000) - source_start) / RATE
            captions.append(
                {
                    "id": f"cap-{len(captions) + 1:02d}",
                    "source": stem,
                    "start": round(max(cursor, start - 0.035), 4),
                    "duration": round(max(0.35, end - start + 0.12), 4),
                    "zh": chinese.replace("语君", "与君").replace("老版", "老板"),
                    "en": english,
                }
            )
        cursor += output_duration

    captions.sort(key=lambda caption: caption["start"])
    for index, caption in enumerate(captions[:-1]):
        next_start = captions[index + 1]["start"]
        caption["duration"] = round(
            max(0.22, min(caption["duration"], next_start - caption["start"] - 0.02)),
            4,
        )

    output = {"rate": RATE, "duration": round(cursor, 4), "clips": timeline}
    (WORK / "timeline.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (WORK / "captions.json").write_text(json.dumps(captions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (WORK / "trim-plan.tsv").write_text("\n".join(trim_lines) + "\n", encoding="utf-8")
    print(json.dumps({"duration": output["duration"], "clips": len(timeline), "captions": len(captions)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
