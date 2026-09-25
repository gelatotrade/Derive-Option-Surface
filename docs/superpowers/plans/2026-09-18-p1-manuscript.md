# Paper 1, Plan 5: Manuscript

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A finished, compact manuscript in Elsevier CAS typesetting that carries the nine figures and otherwise contains as little text as possible. Target length 12 to 13 pages, of which around 5 pages are figures, around 3,800 words of body text.

**Architecture:** The text explains nothing that a figure shows. Every section has a hard word budget and a list of the claims it must make. Numbers appear in the body text only when they carry the argument; everything else is in the figures. Every limitation is stated exactly once, in Section 7, unless it changes how a result is read.

**Tech Stack:** LaTeX, Elsevier CAS (`cas-dc`), tectonic; references in `paper/refs.bib`.

**Language:** The manuscript is in English, like the title and the captions. The project documentation stays in German.

## Global Constraints

- Every number in the body text must be traceable to `results/p1` or to a figure. No number without a reference to the figure that shows it.
- No paragraph repeats what a caption already says.
- Three of the four pre-registered hypotheses are rejected. This is stated in the abstract, not hidden, and the contribution is built on it.
- Limitations exactly once, collected in Section 7. Exception: where a limitation changes how a result is read, a half-sentence stands at that point together with the reference to Section 7.
- No reference without verified fields. Unverified entries carry a `note` field and must not be cited.
- The pilot with cutoff date 2026-09-17 carries the text. Before submission, the final data run with cutoff date 2026-09-30 replaces all numbers; this is why every number in the text also appears in `docs/paper1/NUMBERS.md`.

## Word budget

| Section | Words | carries which figure |
|---|---|---|
| Abstract | 150 | - |
| 1 Introduction | 550 | - |
| 2 The venue and the tape | 450 | - |
| 3 What a markout measures | 550 | T1, T2 |
| 4 Pre-registration and inference | 250 | - |
| 5 Results | 1,100 | F1 to F6 |
| 6 What this means for a maker | 350 | F5 |
| 7 What this cannot show | 250 | A1 |
| 8 Conclusion | 180 | - |
| **Total** | **3,830** | |

Upward deviation of at most ten percent per section. A section that breaks its budget is cut; the budget is not raised.

## Files

| File | Responsibility |
|---|---|
| `paper/main.tex` | Manuscript |
| `paper/refs.bib` | verified references |
| `scripts/p1_wordcount.py` | counts words per section and reports budget overruns |
| `docs/paper1/MANUSCRIPT.md` | acceptance record: word count per section, page count, open items |

---

### Task 1: Scaffold, word counter and acceptance

**Files:**
- Create: `scripts/p1_wordcount.py`, `tests/test_p1_wordcount.py`
- Modify: `paper/main.tex`

**Interfaces:**
- Produces: `sections(tex: str) -> dict[str, int]`, `check(tex_path, budget) -> list[dict]`, CLI `python3 scripts/p1_wordcount.py`
- Counts words per `\section`, excluding figure environments, captions and references.

- [x] **Step 1: Write the test**: a `.tex` snippet with two sections, one figure and one caption; the expectation is that the figure and its caption are not counted and that a broken budget is reported.
- [x] **Step 2: Run the test** → FAIL
- [x] **Step 3: Implement**
- [x] **Step 4: Tests green, commit**

---

### Task 2: Sections 1 to 4, the frame

**Files:** `paper/main.tex`

**What Section 1 must claim (550 words):**
- On a book whose counterparty is visible on chain, it is possible for the first time to measure whom an options maker loses against, instead of guessing it from trade size and aggressiveness.
- The maker's mean markout is positive, but that is almost entirely a statement about the counterparty, not about the option.
- Three contributions: the complete decomposition of the maker margin on a tape with an identified counterparty; the concentration finding and its failure under the usual toxicity measures; the quoting map by delta and tenor.
- Fourth contribution, stated explicitly: four hypotheses fixed before any measurement, three of them rejected. The paper reports the rejections as a result.
- Permitted numbers: +15.70 half spread, −2.65 adverse selection, +8.93 net edge, median 0.98, top-10 share 90.5 percent, dominant makers −25.41 against other takers +24.73.

**What Section 2 must claim (450 words):**
- Derive runs the book off chain and settles on its own OP Stack chain; the mark is not an opinion of the author but an SVI curve that the venue itself writes on chain per expiry.
- The public tape is not anonymous: wallet, subaccount, RFQ identifier, fees, rebate and realised PnL are in it. That is exactly what makes the question measurable.
- Sample, underlyings, period, fill count.
- What is not public: the history of the book, i.e. everything that was quoted and never traded. One sentence, reference to Section 7.

**What Section 3 must claim (550 words), carried by T1 and T2:**
- Definition of the markout and of the sign convention, in two sentences; T1 shows the rest.
- The identity half spread plus adverse selection equals markout, and markout minus fee plus rebate minus hedge equals net edge. One sentence saying that the half spread is contained in the markout and is not counted twice.
- Three mark paths, and why the on-chain curve is the main path. One sentence, reference to A1.
- The four units and why four are needed. Reference to F1.
- The assignment cascade of the counterparty classes in one sentence; F3 shows the rest.

**What Section 4 must claim (250 words):**
- H1 to H4 verbatim, one sentence each, with the rejection rule.
- Inference: clusters on the taker wallet, wild cluster bootstrap with B equal to 9,999 and a fixed seed, instrument-by-day fixed effects, percentile intervals from a pairs bootstrap.
- One sentence on the pre-registration with date and commit, and that two dated addenda exist.

- [x] **Step 1:** Write Sections 1 to 4
- [x] **Step 2:** `python3 scripts/p1_wordcount.py` → every section within budget
- [x] **Step 3:** tectonic builds without overflow
- [x] **Step 4:** Commit

---

### Task 3: Section 5, the results

**Files:** `paper/main.tex`

**1,100 words, six subsections, one per figure. Order and core sentence:**

1. *Reading the number* (F1, 180 words). The mean is not a trading result. Median 0.98 against mean 13.05, contract-weighted 0.264. The three underlyings carry almost the same dollar total at index prices that differ by a factor of 1,599. The reading rule for everything that follows derives from this.
2. *How long adverse selection lasts* (F2, 180 words). On the balanced subset the markout is flat across five horizons. Adverse selection is not what eats the margin. Professional flow lies below zero throughout, the remaining flow above it.
3. *Who the counterparty is* (F3, 200 words). The class means, the cluster counts, the two p-values above five percent. The decisive sentence: the two loss classes already trade at a negative half spread, so they are on the better side of the mark at entry, before adverse selection even sets in. That is a different statement from informed.
4. *Concentration, and why H1 fails* (F4, 200 words). 90.5 percent in ten wallets, a single one accounts for 39 percent, but size and sweep explain nothing under fixed effects. 98.8 and 92.4 percent connect the concentration finding with the class finding.
5. *Where the edge survives, and why H4 fails* (F5, 200 words). 48 of 97 cells positive, three negative, all ETH. The finding flips between zero and one basis point of assumed perp spread. Per notional, the map is monotone in delta and tenor.
6. *The sample is not one market, and why H3 fails* (F6, 140 words). Changes in composition over 33 months, HYPE enters only in November 2025, the MM programme only from November 2024. The DiD estimator lies in the middle of the placebo distribution.

**Rule:** No subsection repeats a number that already appears in an earlier one.

- [x] **Step 1:** Write Section 5
- [x] **Step 2:** Word counter and tectonic
- [x] **Step 3:** Commit

---

### Task 4: Sections 6 to 8, references, abstract

**Files:** `paper/main.tex`, `paper/refs.bib`

**Section 6 (350 words):** What a maker makes of the map. Where to quote, where not, and why the unit is basis points of notional and not USDC per contract. HYPE carries a median of 0.1 to 0.6 basis points and thus practically nothing. One paragraph saying that the concentration is a trading argument: recognising ten addresses is cheaper than modelling size and aggressiveness, because the latter demonstrably explain nothing.

**Section 7 (250 words), each limitation exactly once:** the mark is the venue's own mark, and A1 shows that this does not move the target quantity; path (a) is not a cross-check at 30 minutes; wallets can hold several addresses, so the concentration is a lower bound; the vault class has eight wallets, so H2 is an indication and not a proof; liquidations run outside the trade tape; the vol unit is missing for 10,745 fills; the history of the book is missing, i.e. everything that was quoted and never traded.

**Section 8 (180 words):** What remains when three hypotheses fall.

**Abstract (150 words):** Subject, sample, the decomposition with three numbers, the concentration finding, the three rejections, the sentence for the practitioner.

**References:** take them over from `paper/refs_verified.bib` and cite only verified entries. At a minimum microstructure theory, options microstructure, DeFi market structure, SVI and the bootstrap methodology.

- [x] **Step 1:** Write Sections 6 to 8 and the abstract
- [x] **Step 2:** Insert the references, check every citation against `refs.bib`
- [x] **Step 3:** Check word counter, tectonic and page count
- [x] **Step 4:** Write `docs/paper1/MANUSCRIPT.md`
- [x] **Step 5:** Commit
