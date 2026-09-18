# X article and thread

Two versions of the same story. The article is the long-form post; the thread is what actually travels.
Images are in this folder. Post after the final data run, because every number below is from the pilot cut
to 17 September 2026 and will move slightly.

---

## ARTICLE

**Headline:** Ten wallets take 90% of it

**Subtitle:** I measured 603,940 options fills to find out who a market maker actually loses to. It isn't
the big orders.

---

Every options market maker believes the same thing: somewhere out there is toxic flow, and the way you spot
it is size and aggression. Big order, sweeping through levels, probably informed. Small passive fill,
probably fine.

Nobody has been able to check that properly, because on a normal venue you never learn who was on the other
side. You get a print. You do not get a name.

Derive settles on chain. Its public trade tape carries both wallets, the subaccount, the RFQ id, the fee,
the rebate and the realised PnL of each side. The counterparty is not a statistical construct. It is an
address with a history.

So I took the maker's side of all 603,940 BTC, ETH and HYPE option fills from January 2024 to September
2026, marked every one of them against the volatility surface Derive itself writes on chain, and asked the
question directly.

### First, where the money actually goes

![s1_decomposition.png]

On average the maker earns a half spread of 15.70 USDC per contract and gives back 2.65 to adverse
selection. Fees, rebates and the cost of hedging the resulting delta leave a net edge of 8.93.

Note the size of the adverse selection term. It is small. Everyone worries about it, and it is the second
smallest line on the chart.

### Then, who you traded with

![s2_counterparty.png]

Same instruments. Same surface. Same thirty-minute horizon. The only thing that changes is the address on
the other side, and the result flips from +24.7 to −25.4 USDC per contract.

Look at the wallet counts in brackets. The two negative bars rest on 17 and 33 addresses. The top bar rests
on 10,749.

### And it is even more concentrated than that

![s3_concentration.png]

Ten taker wallets carry 90.5% of the maker's entire aggregate loss. One single address carries 39% of it on
its own. Out of 11,573 taker wallets, only 1,388 are loss-making for the maker at all.

Those same ten wallets supply 98.8% of the fills in the dominant-maker class and 92.4% of the market-maker
programme class. The concentration result and the counterparty result are one finding seen twice.

### Here is the part that surprised me

![s4_proxies.png]

Compare fills above the 90th size percentile against the rest, and sweeps against non-sweeps, and both look
damning. Large and aggressive orders are clearly worse for the maker.

Then control for instrument and day, so you are comparing trades in the same contract on the same date. Both
coefficients collapse. Size: t = −0.74. Sweeps: t = −0.10. Neither is distinguishable from zero.

The raw difference was composition, not information. Big aggressive orders are simply where the professional
addresses trade. Once you hold the contract and the day fixed, the observable shape of an order tells you
nothing about how it will go for you.

The identity tells you everything. The size tells you nothing.

### Where a maker is actually paid

![s5_map.png]

Net edge per unit of notional, which is the unit a quoting decision actually uses. It rises with the
absolute delta and with the tenor, in all three underlyings, and BTC is in a different league.

HYPE sits between 0.1 and 0.6 basis points across the entire surface. After any realistic hedging cost that
is nothing at all.

### The uncomfortable part

I wrote down four hypotheses, their rejection rules and the entire inference procedure, and committed them
before computing a single markout.

Three of the four are rejected.

Toxicity is concentrated, but it is not identifiable from trade characteristics, so H1 fails on its own
second clause. The net edge sits at 49.5% of cells against a threshold of 50%, and whether it clears depends
on an unobserved hedging cost between zero and one basis point, so H4 fails. And an event study around the
listing of HYPE options on a centralised venue has no power on a 33-month panel whose composition changes
underneath it, so H3 fails too.

I am reporting the rejections because that is what a pre-registration is for. It is also the reason you can
believe the one result that survived.

### What I would do with this

If you quote options on this venue, you are not defending against a distribution of order shapes. You are
defending against about a dozen addresses, and on a chain that list is free to build and needs no inference
at all.

Ten wallets, not ten thousand. That is a tractable problem.

The full paper, the code and the pre-registration are here: [LINK]

---

## THREAD

**1/**
Every options market maker thinks toxic flow looks like a big aggressive order.

I checked. On 603,940 fills it doesn't.

It looks like ten wallets. 🧵

**2/**
The problem with this question is that on a normal venue you never learn who traded against you.

Derive settles on chain. The public tape carries both wallets, the fees, the rebate, the realised PnL.

The counterparty isn't a statistic. It's an address.

**3/**
First, where the maker's money goes.

Half spread +15.70. Adverse selection −2.65. Fees, rebate and hedging leave a net edge of +8.93 USDC per
contract.

Adverse selection is the thing everyone fears, and it's the second smallest line here.

![s1_decomposition.png]

**4/**
Now split by who took the other side.

Same instruments, same horizon. +24.7 against ordinary flow, −25.4 against the 17 addresses that dominate
maker volume.

Nothing about the option changed. Only the address did.

![s2_counterparty.png]

**5/**
It gets more extreme.

Ten taker wallets carry 90.5% of the maker's entire loss. One address alone carries 39%.

Of 11,573 taker wallets, only 1,388 are loss-making for the maker at all.

![s3_concentration.png]

**6/**
Here's the part I didn't expect.

Big trades and sweeps look toxic in the raw data.

Control for instrument and day, and both coefficients die. t = −0.74 and t = −0.10.

It was composition, not information. Order shape tells you nothing.

![s4_proxies.png]

**7/**
Where does a maker actually get paid?

Net edge per notional rises with delta and tenor. BTC is in a different league.

HYPE pays 0.1 to 0.6 bp across the whole surface. After hedging, nothing.

![s5_map.png]

**8/**
Full disclosure: I pre-registered four hypotheses before computing anything.

Three are rejected.

That's not a failed study, that's what pre-registration is for, and it's why the surviving result is worth
anything.

**9/**
If you quote here, you're not defending against a distribution of order shapes.

You're defending against about a dozen addresses. On-chain, that list is free.

Ten wallets, not ten thousand.

Paper, code and pre-registration: [LINK]

---

## Notes before posting

- Replace `[LINK]` with the SSRN abstract page, or with the GitHub repository if the paper is not up yet.
- Every number is from the pilot cut to 17 September 2026. Re-render the cards after the final run and
  re-check the six numbers that appear in the text.
- The cards are 1600 x 900 PNG, which is the aspect X renders without cropping in both article and timeline.
- Keep the framing neutral about the professional addresses. They are running a normal strategy, and the
  paper says their advantage is the entry price rather than private information.
