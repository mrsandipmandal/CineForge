# CineForge Third-Party Licenses & Dependency Inventory

**Audit Date:** 2026-11-06  
**Auditor:** Senior Software Licensing & Compliance Engineer  

---

## 1. Bundled Assets & Datasets

### 1.1 Fonts
| Asset | Path | Copyright Holder | License | Permitted Uses | Requirements |
|---|---|---|---|---|---|
| **Patrick Hand** | `ink-theater/assets/patrickhand.ttf` | Patrick Wagesreiter | SIL Open Font License 1.1 | Personal & Commercial | Bundle OFL.txt; do not sell font standalone |
| **Playfair Display** | `remotion-composer/src/fonts/` | Claus Eggers Sørensen | SIL Open Font License 1.1 | Personal & Commercial | Retain OFL license notice |
| **Space Grotesk** | `remotion-composer/src/fonts/` | Florian Karsten | SIL Open Font License 1.1 | Personal & Commercial | Retain OFL license notice |

### 1.2 Motion Capture Data
| Asset | Path | Source / Copyright | License | Permitted Uses |
|---|---|---|---|---|
| **CMU Mocap Clips** | `ink-theater/mocap/clips/*.json`, `clips.js` | Carnegie Mellon University Graphics Lab | CMU Free License | Free for all research and commercial projects worldwide |

### 1.3 Vendored Agent Skills
| Skill Family | Path | Upstream Origin | License | Compliance Status |
|---|---|---|---|---|
| **HyperFrames Skills** (12 skills) | `.agents/skills/hyperframes*` | HeyGen (`heygen-com/hyperframes`) | MIT / Apache-2.0 | Properly documented in `PROVENANCE.md` |
| **GSAP Skills** (8 skills) | `.agents/skills/gsap*` | GreenSock (`greensock/gsap-skills`) | MIT License | Properly documented in `.agents/skills/gsap/README.md` |

---

## 2. Python Direct Dependencies (`requirements.txt`)

All declared Python dependencies in `requirements.txt` are permissively licensed:

| Package | Version Constraint | License Type | Commercial Use | Copyleft Conflict |
|---|---|---|---|---|
| **pyyaml** | `>=6.0` | MIT License | Allowed | None |
| **pydantic** | `>=2.0` | MIT License | Allowed | None |
| **jsonschema** | `>=4.20` | MIT License | Allowed | None |
| **python-dotenv** | `>=1.0` | BSD-3-Clause | Allowed | None |
| **Pillow** | `>=10.0` | HPND (MIT-like) | Allowed | None |
| **numpy** | `>=1.24` | BSD-3-Clause | Allowed | None |
| **requests** | `>=2.31` | Apache-2.0 | Allowed | None |
| **google-auth** | `>=2.0` | Apache-2.0 | Allowed | None |
| **google-genai** | `>=1.0.0` | Apache-2.0 | Allowed | None |
| **openai** | `>=2.44.0` | Apache-2.0 | Allowed | None |
| **fastapi** | `>=0.110` | MIT License | Allowed | None |
| **uvicorn** | `>=0.29` | BSD-3-Clause | Allowed | None |
| **watchfiles** | `>=0.21` | MIT License | Allowed | None |
| **websockets** | `>=14.0` | BSD-3-Clause | Allowed | None |
| **pytest** | `>=8.0` | MIT License | Allowed | None |
| **httpx** | `>=0.24` | BSD-3-Clause | Allowed | None |

> [!NOTE]
> None of the Python direct dependencies introduce copyleft conflicts with AGPL-3.0. Permissive licenses (MIT, BSD, Apache-2.0) can be combined with AGPL-3.0 software.

---

## 3. Node.js / Remotion Dependencies (`remotion-composer/package.json`)

| Package | Version | License | Note on Commercial Use |
|---|---|---|---|
| `react`, `react-dom` | `^18.2.0` | MIT | Free for all uses |
| `d3-geo` | `^3.1.1` | ISC | Free for all uses |
| `fast-uri` | `^3.1.5` | MIT | Free for all uses |
| `topojson-client` | `^3.1.0` | ISC | Free for all uses |
| `world-atlas` | `^2.0.2` | ISC | Free for all uses |
| `remotion` & `@remotion/*` | `^4.0.484` | **Remotion License** | **Free for individuals, non-profits, and companies <= 3 people.** Commercial license required for companies >= 4 people. |

> [!WARNING]
> Remotion's license imposes its own commercial restrictions on entities with 4 or more employees. This is external to AGPL-3.0, but must be observed if CineForge is deployed commercially.
