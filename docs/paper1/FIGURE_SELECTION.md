# How the nine figures were selected

2026-09-18. Three independent draft sets of eight figures each (perspectives: mechanism, empirics, practitioner),
followed by two judges with different lenses: a referee who recomputed the claims against the result files, and a
design review for legibility in two-column CAS typesetting at 8 pt in greyscale.

## Where the judges agreed

| Slot | Both | Why |
|---|---|---|
| T1 | P-T1 | The only figure that carries three mark paths and three units on 2.8 inches, because all panels share the same x axis. |
| T2 | E-T2 together with P-T2 | The referee wanted P-T2's fee hexbin as the third panel of E-T2, and the design review wanted the same merger from the other side. |
| Concentration | E4 | The only version that shows both parts of the H1 rule: the concentration and the coefficients on which H1 fails. |
| Cell map | E5 | The only grid figure with a poolable unit and with effect size and reliability shown separately. |

## Where they diverged, and how it was decided

**Class figure: E3 versus P2.** The referee wanted E3, because only there does it say how few wallets carry a class.
The design review wanted P2, because its bar per class is legible and E3's swarm of 10,749 points prints as a black
block. Decided: P2's layout with E3's numbers. The finding that 98.8 per cent of the fills of the dominant makers and
92.4 per cent of the MM-programme fills come from exactly the ten loss wallets from H1 has been recomputed and stays.

**Units figure: E1 versus P4.** The referee wanted E1 as a reading rule ahead of all results. The design review rated E1
a 5, because its log axis, normalised to the overall mean, can flip at a reference value of 0.264, but it praises
E1's panel b. Decided: P4 as the carrier, extended by E1's panel b. Both findings stay, and the dangerous axis
is dropped.

**Mark quality: main text or appendix.** The referee wanted EA1 in the main text, because this will be the most heavily
attacked point. The design review wanted P-A1 in the appendix and considered EA1, with five plotting areas, overloaded.
Decided: appendix, but as a single condensed figure drawn from both, and referenced early in the text. The exonerating
finding is a null relationship, and a null relationship does not need a main-text slot.

## The gap that no draft covered

None of the 21 figures had a calendar axis. Three consequences: H3 would have been the only pre-registered hypothesis
without a figure, although it is the only one with an event, a window and 100 placebos. The sample spans 33 months
and is demonstrably not homogeneous: the MM-programme class can only be assigned from 2024-11-20 onward, and HYPE only
enters the sample on 2025-11-10. And the one wallet that carries 39.0 per cent of the maker loss could have been active
for only a few months. That is why there is F6, with a shared monthly axis.

One correction to the jury verdict: the referee gives 2025-10-24 as the date HYPE enters. Recomputed, the first
HYPE fill in the sample is on 2025-11-10 22:06 UTC, with zero fills before it.

## What went straight from the review into the code

The referee found a contradiction that has nothing to do with figures: the headline number for H4 was computed with
9,999 bootstrap draws, the sensitivity table with 1,999, and exactly one cell tipped across the rejection threshold
as a result. Fixed, recomputed, and secured with a guard on the mechanism. The verdicts on H1
to H4 do not change. After the rerun, the p-values of the two conspicuous classes are 0.1003 and
0.1013 instead of 0.1065 and 0.0940, and the sensitivity at zero basis points is 57.7 instead of 55.7 per cent.

## What the recomputation corrected in the drafts

| Claim in a draft | Recomputed |
|---|---|
| HYPE enters the sample on 2025-10-24 | first HYPE fill on 2025-11-10, none before |
| 3.6 per cent of fills pay more in fees than in premium | holds for the taker, and it is 2.40 per cent; the maker pays nothing at all on 66.9 per cent of fills |
| five per cent trimmed mean 10.80 | 6.36 |
| Markout as a share of the premium, q25 -3.3 / median +3.4 / q75 +13.5 per cent | -1.6 / +1.1 / +21.1 |
| Per-contract factor of 426 between the underlyings | 1,599 between BTC and HYPE, measured at the average index price |

## Addendum 2026-09-25

Two rows above are superseded by Addendum 3 to the pre-registration. The draft's quartiles, -3.3 / +3.4 /
+13.5 per cent, were the unit-consistent form (markout per contract divided by price per contract) and apply again; the
"recomputation" -1.6 / +1.1 / +21.1 divided the markout per contract by the premium of the whole fill. After the
fee-unit correction, the sensitivity at zero basis points is 78.4 instead of 57.7 per cent.
Details: `docs/paper1/FINDING_2026-09-25_FEE_UNITS.md`, `docs/paper1/REVISION_2026-09-25.md`.
