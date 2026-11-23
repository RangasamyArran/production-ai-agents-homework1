# Homework 1 — GPU Media Worker: step by step

Path: **Sana (text-to-image) on a preemptible L40S Endpoint, called from your laptop** — the course's default, cheapest path. Expected cost: well under $1.

## 0. Once: credits
1. https://console.nebius.com → **Billing → Apply promo code** → enter your AI Cloud code. Confirm the balance went up in **Billing → Transactions**.
2. Check today's preemptible L40S price (`1gpu-8vcpu-32gb`, your region) at https://nebius.com/prices. The script defaults to **$0.75/h** (course reading, 2026-11-16) — pass `--price X` if yours differs.

## 1. Make the idea yours (optional)
Open `homework1.py` and edit `IDEA`, `CHARACTER`, `STYLE`, `PAGES` (10 prompts). Default idea: a 10-page bedtime storybook about Pip, an otter lighthouse keeper. No real people, brands or known characters.

## 2. Create the Endpoint
1. Open https://console.nebius.com/serverless/endpoint/create?template=sana (1× L40S, preemptible, token auth).
2. Generate the token and **copy it before clicking Create** (shown once). Don't paste it in chats or screenshots.
3. Click **Create**, copy the Endpoint's HTTPS URL. **Note the time** you clicked Create.

## 3. Run the script immediately
```bash
python3 homework1.py
```
- Paste the URL and token (token is hidden). Or put `ENDPOINT_URL=...` and `ENDPOINT_TOKEN=...` in a `.env` next to the script (don't commit it).
- It polls until the model answers (startup + model load: a few minutes).
- It asks how many seconds from **Create → RUNNING** — read that from the Endpoint page in the console. This splits startup vs model load. (Blank = all counted as load; the fixed total is the same either way.)
- It then generates 10 images, times each, and prints Q6/Q7.
- Output: `runs/<timestamp>/page-01.png … page-10.png` and `metrics.json`.

If your price turns out different, recompute without re-running:
```bash
python3 homework1.py --recost runs/<timestamp>/metrics.json --price 0.75
```

## 4. STOP the Endpoint
Console → Endpoint → **Stop** (or Delete). Confirm status `STOPPED`. Check **Billing → Usage** the next day.

## 5. How the cost is computed (lesson 05)
- Fixed time = startup + model load → **F = fixed_s × price/3600**
- Per-asset **c = median generation time × price/3600** (the median keeps the slow first warm-up call out)
- **Cost per asset at N = F/N + c**; Question 7 uses N = 1000.

## 6. Answer sheet — storybook run (runs/20261123-210928/)
| Q | Answer |
|---|---|
| 1. Idea | A 10-page bedtime storybook about Pip, a small otter who keeps a lighthouse. I chose it because storybook pages need the same character in every scene, which is the consistency problem this course is about, and I can reuse the character in Homework 3. |
| 2. Model | Sana 1600M 1024px (`Efficient-Large-Model/Sana_1600M_1024px_diffusers`) |
| 3. Modality | Image |
| 4. How | Endpoint |
| 5. GPU | L40S |
| 6. Median s/asset | **2.96** |
| 7. Cost/asset at N=1000 (USD) | **0.000655** |

Submit: https://courses.datatalks.club/production-ai-agents-generative-media/homework/module1

## 7. Learning in public (LinkedIn)
```text
Completed Module 1 of Production AI Agents for Generative Media!

I ran Sana 1600M on Nebius Serverless AI (preemptible L40S) and generated a 10-page storybook about Pip, an otter lighthouse keeper (images attached).
It takes 2.96 s to generate one image (median of 10).
At 1000 images, one costs about $0.00066 (~0.07 cents).

The idea: keeping one character consistent across scenes. The same seed and prompt give the same image, but a new scene changes the character, which is the problem the next modules tackle.

My code: <LINK>

@DataTalksClub @Nebius
```

## 8. Run log (2026-11-23, eu-north1, preemptible L40S, $0.75/h)
Storybook run (submitted) — runs/20261123-210928/
- Startup 130.3 s + model load 55.6 s = 185.9 s fixed -> F = $0.0387
- 10 images: first 6.78 s (warm-up), then 2.75-3.04 s; median 2.96 s -> c = $0.000617
- Cost per image: N=1 $0.0393, N=10 $0.0045, N=1000 $0.000655
- Whole 10-image run cost about $0.046

SMC run (not submitted) — runs/20261123-211754/: median 2.77 s, $0.000615 at N=1000. Sana didn't draw the SMC concepts.
