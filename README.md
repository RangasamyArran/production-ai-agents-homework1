# Production AI Agents for Generative Media: Homework 1

A GPU media worker: generate 10 images in one run on a Nebius Serverless AI Endpoint, time each step, and work out the cost per asset.

The course is [DataTalksClub/production-ai-agents-for-media-generation](https://github.com/DataTalksClub/production-ai-agents-for-media-generation). This homework follows [Module 1](https://github.com/DataTalksClub/production-ai-agents-for-media-generation/tree/main/01-consistent-media-generation-on-serverless-gpus) and [its homework](https://github.com/DataTalksClub/production-ai-agents-for-media-generation/blob/main/cohorts/2026/homework/01-consistent-media-generation-on-serverless-gpus/homework.md).

## What it does

`homework1.py` uses only the Python standard library. It:

1. Waits until the Endpoint's `/v1/models` answers.
2. Generates 10 images with Sana (`Efficient-Large-Model/Sana_1600M_1024px_diffusers`) through `/v1/images/generations`.
3. Times each image and saves the PNGs and a `metrics.json` in `runs/<timestamp>/`.
4. Calculates the cost per asset from the fixed cost of the run (startup and model load) plus the cost of each image, following [lesson 05](https://github.com/DataTalksClub/production-ai-agents-for-media-generation/blob/main/01-consistent-media-generation-on-serverless-gpus/05-measuring-costs.md):
   - Fixed cost **F** = (startup + model load) × price per second
   - Cost per asset **c** = median generation time × price per second
   - Projected cost per asset at N assets = **F / N + c**

## Setup

You need Python 3.9 or newer, and an Endpoint created from the [Sana template](https://console.nebius.com/serverless/endpoint/create?template=sana) in **eu-north1**, on a preemptible L40S.

```bash
python3 homework1.py
```

The script asks for the Endpoint URL and token. The token is typed with hidden input and is never printed or saved to the repository. You can also set `ENDPOINT_URL` and `ENDPOINT_TOKEN` in a `.env` file next to the script; `.env` is git-ignored.

Options:

| Option | Purpose |
|---|---|
| `--price 0.75` | Price in USD per GPU-hour your run paid (default `0.75`, the eu-north1 preemptible L40S price read on 2026-11-16) |
| `--startup-s` / `--load-s` | Times in seconds read from the Endpoint's logs, so the script doesn't ask |
| `--recost runs/<timestamp>/metrics.json` | Recalculate costs from a saved run without using the GPU |

Edit `IDEA`, `CHARACTER`, `STYLE` and `PAGES` at the top of `homework1.py` to change the images.

**Stop the Endpoint** in the console as soon as the run finishes. It bills while it is `RUNNING`, even when idle.

## Results

| Run | Idea | Median per image | Cost per image at N = 1,000 | Status |
|---|---|---|---|---|
| [`runs/20261123-210928`](runs/20261123-210928) | Pip the otter's storybook (10 pages) | 2.96 s | $0.000655 | Submitted |
| [`runs/20261123-211754`](runs/20261123-211754) | Smart Money Concepts cards, first prompts | 2.77 s | $0.000615 | Not submitted |
| [`runs/20261123-213152`](runs/20261123-213152) | Smart Money Concepts cards, revised prompts | 2.54 s | $0.000557 | Not submitted; model-load time not recorded (0 s) |

Startup and model load for the storybook run were 130.3 s and 55.6 s, so the fixed cost was $0.0387 per run at $0.75 per hour.

**What I learned:** Sana keeps a style well but doesn't reliably draw abstract concepts. The Smart Money Concepts cards look alike, and most don't show their concept. The storybook images share one style, and the two pages checked show Pip clearly, but the scarf colour changes between them. The same seed and prompt give the same image, while a new scene changes the character's details. That is the consistency problem the course addresses in later modules.

The SMC images are educational illustrations only, not trading advice.

## Files

| Path | What it is |
|---|---|
| `homework1.py` | The script: generation, timing and cost |
| `HOMEWORK_GUIDE.md` | Step-by-step guide, the answer sheet and the LinkedIn post |
| `runs/` | Saved images and `metrics.json` for each run |
| `pyproject.toml`, `uv.lock`, `.python-version`, `src/` | Project setup from `uv` |

## Cleanup

Stop or delete every Endpoint you created, and check **Billing → Usage** the next day to make sure nothing is still billing.
