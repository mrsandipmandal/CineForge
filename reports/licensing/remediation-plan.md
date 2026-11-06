# CineForge License Compliance & Remediation Plan

**Audit Reference:** AGPL-3.0 & Copyright Provenance Audit  
**Target:** Restore Full Legal Compliance under GNU AGPL-3.0  

---

## 1. Compliance vs. Documentation Actions

To address the audit findings, remediation actions fall into two distinct categories:

1. **Substantive Legal Compliance Actions:** Essential legal remedies required to avoid copyright infringement, cure automatic license termination under AGPL-3.0 Section 8, and prevent legal claims from upstream authors.
2. **Hygiene & Documentation Improvements:** Best practices that ensure clarity, align metadata across tools, and prevent confusing downstream users.

---

## 2. Remediation Priority Table (What Must Change)

| No. | File / Module | Current Problem | Exact Required Action | Expected Result | Rewrite Required? |
|---|---|---|---|---|---|
| **1** | `LICENSE` | Unauthorized replacement of AGPL-3.0 with Apache-2.0 ("Copyright 2026 Sandip Mandal") | Restore the full, official GNU AGPL-3.0 text verbatim. Remove the Apache 2.0 text and the false copyright claim. | Complies with AGPL-3.0 Section 4 & Section 5(b); cures Section 8 termination risk. | **NO** (Restore original file) |
| **2** | `AUTHORS.md` / `NOTICE` | Upstream copyright owners and contributors are not credited anywhere in the repository. | Create `AUTHORS.md` acknowledging Calesthio and the OpenMontage contributors, and create a `NOTICE` file documenting the origin fork. | Preserves moral rights and copyright attribution per Berne Convention and Section 4. | **NO** (Documentation addition) |
| **3** | 216 Modified Files (Code & Config) | Files were modified (or project renamed) without AGPL Section 5(a) modification notices. | Add a prominent modification header to all modified files: `Modified from OpenMontage by CineForge contributors on 2026-11-06 under GNU AGPL-3.0`. | Full compliance with AGPL-3.0 Section 5(a). | **NO** (Notice insertion) |
| **4** | `backlot/server.py` & `backlot/ui/` | Network users of Backlot live board receive no offer or download mechanism for Corresponding Source. | Add a "Source Code" button / link in `board.html` header pointing to the repository source and an API route (`/api/source/download`) serving a source tarball. | Full compliance with AGPL-3.0 Section 13 (Remote Network Interaction). | **NO** (Feature addition) |
| **5** | `.github/workflows/security.yml` | Line 220 in Dependency Review denies `AGPL-3.0, GPL-3.0, GPL-2.0` licenses in an AGPL repository. | Remove `AGPL-3.0` from `deny-licenses` in the workflow step. | Eliminates internal CI/CD policy conflict. | **NO** (Config correction) |
| **6** | `README.md` & `README_zh-CN.md` | Minor wording claims CineForge is an independent creation while displaying AGPLv3 badge. | Update README to clearly state: "CineForge is a fork and extension of OpenMontage, licensed under GNU AGPL-3.0." | Accurate repository metadata and transparency. | **NO** (Text edit) |
| **7** | `setup.py` & `remotion-composer/package.json` | License metadata fields either omit AGPL-3.0 or fail to specify it. | In `setup.py`, add `license="GNU AGPLv3"` and classifier `'License :: OSI Approved :: GNU Affero General Public License v3'`. In `package.json`, set `"license": "AGPL-3.0-only"`. | Correct package distribution metadata. | **NO** (Metadata update) |
| **8** | `THIRD_PARTY_LICENSES.md` | Bundled third-party fonts (OFL 1.1), CMU mocap data, and vendored skills lack a unified summary. | Create `THIRD_PARTY_LICENSES.md` consolidating notices for Patrick Hand font, CMU mocap, HeyGen HyperFrames, and GreenSock GSAP skills. | Clear third-party licensing documentation. | **NO** (Documentation addition) |

---

## 3. Step-by-Step Remediation Roadmap

### Phase 1: Immediate Legal Cure (Within 24 Hours)
1. **Restore `LICENSE`:**
   - Replace root `LICENSE` with the official GNU AGPL-3.0 text from upstream commit `d21f5d4`.
   - Delete the Apache 2.0 text and the "Copyright 2026 Sandip Mandal" assertion.
2. **Acknowledge Upstream Copyright:**
   - Add `AUTHORS.md` listing Calesthio and referencing the upstream contributor commit history.

### Phase 2: Modification & Notice Standardization
1. **Add Section 5(a) Notices:**
   - Use an automated script to prepend standard SPDX headers and modification notices to all Python, TypeScript, and Schema files modified in CineForge.
   - Example header:
     ```python
     # SPDX-License-Identifier: AGPL-3.0-or-later
     # Copyright (C) 2026 Calesthio and OpenMontage contributors
     # Portions Copyright (C) 2026 Sandip Mandal
     # Modified in 2026 for CineForge
     ```
2. **Correct `.github/workflows/security.yml`:**
   - Modify line 220 so that AGPL-3.0 is not treated as a forbidden license.

### Phase 3: Network Transparency (Section 13 Implementation)
1. **Backlot UI Source Link:**
   - In `backlot/ui/board.html`, add an element in the top navigation bar:
     `<a href="https://github.com/mrsandipmandal/CineForge" target="_blank" class="nav-source-link">Source Code (AGPLv3)</a>`
   - In `backlot/server.py`, add an endpoint `/api/source` returning the commit SHA, repository URL, and license terms.
