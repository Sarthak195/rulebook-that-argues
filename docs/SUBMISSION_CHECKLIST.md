# Submission checklist

Deadline: Tuesday 8 September 2026, 8:00 pm IST.

## 1. Repository link (paste first)

```
https://github.com/Sarthak195/rulebook-that-argues
```

Problem: **1, The Rulebook That Argues With Itself**. The repository is public, the README says
how to run it and that nothing is mocked, and the commit history goes from scaffold to corpus
to pipeline to evaluation to deployment.

## 2. Before recording

- Open http://34.93.55.172/ (or the HTTPS tunnel URL in `docs/DEPLOYMENT.md`, or run locally
  with `uvicorn app.main:app`). The header must show a `gemini#…/gemini-3.5-flash-lite` model and
  "models live".
- Open the `Evaluation` view; a finished 47/47 run is already there. If you want a fresh one,
  click `Run all questions` and let it finish (several minutes on one free Gemini project). The
  run happens on the server, so you can refresh or leave the page; the finished table stays there.
- Ask one question in the first tab to warm up.
- Read `docs/VIDEO_SCRIPT.md` once. It is timed at about three minutes.
- Single answers take about 2 seconds, 3 to 4 with the verification pass. Do not cut waits out
  of the video; say "free tier" and let it load.

## 3. Record (2 to 3 minutes)

Follow the script. The order matters: start the Evaluation run first so it is finished by the
time you come back to it.

If the evaluation shows a failure or two, do not re-record. Tick "show failures only", read the
detail column, and say whether you agree with the model. The README already explains that the
free model varies run to run and how the validator and audit escalation deal with it.

## 4. Upload and paste

Google Drive, share as "Anyone with the link, Viewer", paste the link in the portal's step 2.

## 5. After the round

The VM costs about USD 0.02 per hour. Stop it:

```
gcloud compute instances stop rulebook-vm --zone asia-south1-a
```

Delete it and the static IP when the result is out:

```
gcloud compute instances delete rulebook-vm --zone asia-south1-a
gcloud compute addresses delete rulebook-ip --region asia-south1
```

## If you have time to spare

- Replace the `Demo video: link goes here` line in the README with the Drive link and push.
- Run `python scripts/ui_test.py http://34.93.55.172` once more and glance at `docs/img/`.
