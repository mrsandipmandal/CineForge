# GNU AGPL-3.0 Compliance Audit Report — CineForge

**Product:** CineForge AI Film Production Studio  
**Audit Date:** 2026-11-06  
**Auditor:** Senior Software Licensing & Compliance Engineer  
**Upstream Repository:** `https://github.com/calesthio/OpenMontage.git`  
**Upstream License:** GNU Affero General Public License Version 3.0 (AGPL-3.0)  
**Upstream Base Commit:** `d21f5d4eaa08422b09c7091757a05affcbabb35b`  
**CineForge Current Head:** `541dbbd` (branch `feature/openmontage-matrix-upgrade`)  

---

## 1. Executive Compliance Evaluation

| Compliance Check | Status | Severity | Primary Finding |
|---|---|---|---|
| **Section 4 — Verbatim Copies & License Preservation** | **FAILED** | **CRITICAL** | Upstream `LICENSE` (AGPL-3.0) was deleted and replaced with Apache-2.0. |
| **Section 5(a) — Prominent Modification Notices** | **FAILED** | **HIGH** | 216 modified files lack prominent modification notices and change dates. |
| **Section 5(b) — License Notices on Modified Works** | **FAILED** | **HIGH** | Contradictory license statements across `README.md` (AGPLv3) and `LICENSE` (Apache-2.0). |
| **Section 5(c) — Copyleft Scope (Work as a Whole)** | **FAILED** | **CRITICAL** | Claiming Apache-2.0 or attempting proprietary/non-commercial licensing on the combined work violates Section 5(c). |
| **Section 6 — Conveying Non-Source Forms** | **WARNING** | **MEDIUM** | Built wheels and containerized deployments must include Corresponding Source offer. |
| **Section 7 — Prohibition of Further Restrictions** | **FAILED** | **CRITICAL** | Attempting to impose a Non-Commercial / Personal-Use-Only restriction on AGPL-3.0 code is strictly prohibited. |
| **Section 10 — Downstream Licensing Rights** | **FAILED** | **HIGH** | Upstream licensors' rights to downstream recipients are obscured by relicensing claims. |
| **Section 13 — Remote Network Interaction** | **FAILED** | **HIGH** | Modified `Backlot` live studio server lacks a network-facing Corresponding Source offer/link. |

---

## 2. In-Depth Analysis of Applicable AGPL-3.0 Sections

### 2.1 Section 4 — Conveying Verbatim Copies
> *"You may convey verbatim copies of the Program's source code as you receive it, in any medium, provided that you conspicuously and appropriately publish on each copy an appropriate copyright notice; keep intact all notices stating that this License and any non-permissive terms added in accord with section 7 apply to the code; keep intact all notices of the absence of any warranty; and give all recipients a copy of this License along with the Program."*

- **Audit Findings:**
  1. In commit `470cdd5c07d6bd6147de8db07e1eca7298e97e0d` ("first commit"), the original `LICENSE` file containing the text of the GNU Affero General Public License Version 3 was completely removed (864 lines deleted).
  2. A 203-line Apache License 2.0 was inserted, ending with an unauthorized copyright claim:
     ```
     Reverse Engineer Everything
     Copyright 2026 Sandip Mandal
     Licensed under the Apache License, Version 2.0
     ```
  3. Over 1,980 files are byte-for-byte verbatim copies of `calesthio/OpenMontage` files. Distributing these files under an Apache 2.0 header constitutes copyright infringement and a breach of Section 4.

### 2.2 Section 5 — Conveying Modified Source Versions
> *"You may convey a work based on the Program, or the modifications to produce it from the Program, in the form of source code under the terms of section 4, provided that you also meet all of these conditions:*
> *a) The work must carry prominent notices stating that you modified it, and giving a relevant date.*
> *b) The work must carry prominent notices stating that it is released under this License and any conditions added under section 7.*
> *c) You must license the entire work, as a whole, under this License to anyone who comes into possession of a copy..."*

- **Audit Findings:**
  1. **Violation of 5(a):** Exactly 216 files were modified from upstream. 195 of these files were modified by a repository-wide string replacement renaming `OpenMontage` to `CineForge` (commit `94fdad2`). 21 files received functional or architectural additions (e.g. `backlot/server.py`, `backlot/ui/board.js`, `tools/audio/tts_selector.py`, `schemas/artifacts/scene_plan.schema.json`). Not a single file carries a Section 5(a) modification notice stating who modified it, what was modified, and the date of modification.
  2. **Violation of 5(b):** The modified source is falsely labeled as Apache-2.0 in `LICENSE`, despite `README.md` displaying an AGPLv3 shield badge.
  3. **Violation of 5(c):** Under Section 5(c), the copyleft scope covers CineForge *as a whole*. The entire CineForge repository must be licensed under AGPL-3.0. Splitting off the modifications or claiming proprietary rights over the combined work is a direct violation.

### 2.3 Section 7 & Section 10 — Prohibition of Further Restrictions
> *"You may not place any further restrictions on the exercise of the rights granted or affirmed under this License... If the Program as you received it, or any part of it, contains a notice stating that it is governed by this License along with a term that is a further restriction, you may remove that term."* (Section 7)
> *"Each time you convey a covered work, the recipient automatically receives a license from the original licensors... You may not impose any further restrictions on the exercise of the rights granted or affirmed under this License."* (Section 10)

- **Audit Findings:**
  1. The project owner wishes to enforce a "Personal-Use-Only" and "Non-Commercial" policy (prohibiting commercial use, SaaS, paid hosting, resale).
  2. Under free software licensing jurisprudence and the express language of AGPL-3.0 Section 7, a "Non-Commercial" restriction is an unauthorized "further restriction".
  3. A licensee cannot add a Non-Commercial clause to upstream AGPL-3.0 code. If such a clause is added, Section 7 allows any downstream user to treat the clause as void and strip it off, or the entire license terminates under Section 8.

### 2.4 Section 13 — Remote Network Interaction
> *"Notwithstanding any other provision of this License, if you modify the Program, your modified version must prominently offer all users interacting with it remotely through a computer network (if your version supports such interaction) an opportunity to receive the Corresponding Source of your version by providing access to the Corresponding Source from a network server at no charge, through some standard or customary means of facilitating copying of software."*

- **Audit Findings:**
  1. CineForge is modified from OpenMontage.
  2. CineForge includes `backlot/` — a live FastAPI web application serving an interactive Single Page Application (`board.html`, `board.js`) over HTTP and Server-Sent Events (SSE).
  3. Backlot is specifically built to run as a server (`backlot open <project-id>`, `server.py`). If this server is bound to a network interface and accessed by remote users across a local network or the Internet, AGPL-3.0 Section 13 is triggered.
  4. Inspection of `backlot/ui/board.html`, `backlot/ui/index.html`, and `backlot/server.py` reveals that **no "Source Code" link, download button, or API endpoint for Corresponding Source exists in the UI**.
  5. Any network deployment of CineForge currently violates Section 13.

### 2.5 CI/CD & Dependency Governance Contradiction
- In `.github/workflows/security.yml` line 220, the automated dependency review gate is configured as follows:
  ```yaml
  with:
    fail-on-severity: high
    deny-licenses: "AGPL-3.0, GPL-3.0, GPL-2.0"
  ```
- **Finding:** The CI workflow explicitly forbids `AGPL-3.0` dependencies from being added, while the host repository itself is derived from an AGPL-3.0 codebase. This demonstrates a fundamental misunderstanding of the repository's legal provenance.

---

## 3. License Termination Risk (Section 8)

Section 8 of AGPL-3.0 states:
> *"You may not propagate or modify a covered work except as expressly provided under this License. Any attempt otherwise to propagate or modify it is void, and will automatically terminate your rights under this License (including any patent licenses granted under the third paragraph of section 11)."*

Because CineForge:
1. Replaced AGPL-3.0 with Apache-2.0,
2. Removed upstream copyright notices,
3. Failed to provide Section 5(a) modification notices,
4. Fails to provide Section 13 network source access in Backlot,

The repository currently operates in a state of **automatic license termination** under Section 8. Under Section 8, rights are only reinstated if the copyright holder explicitly excuses the violation, or if the violation is cured within 30 days after receiving notice.

---

## 4. Remediation Requirements Summary

To regain full compliance with GNU AGPL-3.0:
1. **Restore `LICENSE`:** Revert `LICENSE` to the official, unaltered GNU AGPL-3.0 text.
2. **Add `AUTHORS.md` / `NOTICE`:** Acknowledge Calesthio and all upstream OpenMontage contributors.
3. **Add Modification Notices:** Add header comments to modified files per Section 5(a).
4. **Implement Section 13 Source Link:** Add a prominent "Source Code" link in the Backlot UI navigation header pointing to the repository or providing a tarball download.
5. **Fix CI/CD Configuration:** Remove `AGPL-3.0` from `deny-licenses` in `.github/workflows/security.yml`.
6. **Correct Metadata:** Align `setup.py`, `package.json`, and README documentation with GNU AGPL-3.0.
