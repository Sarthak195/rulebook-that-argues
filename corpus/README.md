# Corpus

A rulebook for a fictional Indian engineering college, **Shivalik Institute of Technology, Indore**,
modelled on the structure of typical B.Tech. regulations (attendance, evaluation, grading, hostel,
fees, scholarships, leave). Every word was written for this project. No real institution's text is
reproduced, so the contradictions could be placed exactly where we wanted them.

| File | Code | Format | What it covers |
|---|---|---|---|
| `01_academic_regulations.md` | AR | markdown | programme structure, registration, attendance, evaluation, grading, promotion, supplementary exams, re-evaluation, break of study, scholarships, fees and dues, misconduct, power to relax |
| `02_examination_regulations.md` | EE | markdown | exam conduct, permitted materials, absence from exams, unfair means, moderation, results, supplementary fee, practicals |
| `03_hostel_handbook.md` | HH | markdown | allotment, gate timings, visitors, mess, prohibited items, fines, vacating, health |
| `04_fee_schedule.md` | FS | markdown **tables** | fee components, payment deadlines, late fee, refund on withdrawal, payment mode |
| `05_scholarship_policy.pdf` | SF | **PDF** (built from `src/05_scholarship_policy.md` by `scripts/build_pdf.py`) | scholarship categories, continuation conditions, application, disbursement, concessions and refunds, grievances |
| `06_leave_and_medical_policy.md` | LM | markdown | medical certificates, condonation, hospitalisation, deputation, bereavement, placement leave, health services |

Section ids used in citations are `<code> §<section>`, for example `AR §4.3`.

The three planted contradictions are recorded in [`CONTRADICTIONS.md`](CONTRADICTIONS.md).
The system never reads that file; it is the answer key for the evaluation.
