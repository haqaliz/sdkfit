# Name and handles check

Checked live on **2026-11-16**. This is a launch-risk record, not legal advice.

## Findings

| Surface | Status | What is there |
|---|---|---|
| **tenonhq.com** | **Active company** | Tenon — marketing automation built on ServiceNow, with a $8M Series A (2023). This is a direct brand/domain collision with the distribution name `tenonhq`. |
| PyPI `tenon` | Taken | An unrelated captcha package (`tenon` 0.1.7). |
| PyPI `tenonhq` | Free (404) | Available, but reads as the domain of the active company above. |
| npm `tenon` | Taken | `tenon` 2.0.21, the front-end package for Tenon 2.x (the accessibility product). |
| tenon.io | Retired | Redirects to Level Access' Tenon retirement FAQ. |
| tenon.com | Legacy | Tenon Intersystems, software company since 1989. |
| GitHub | Crowded | Tenon CMS (Rails), `Tenon-Net/TenonAdmin`, a low-code platform and others. |
| Product Hunt | No exact product found | No product profile for `tenon`; a 365-day launch search found no exact match. |

## Risk

- A Product Hunt launch named **Tenon** will be confused with the active **tenonhq.com** company and
  with the older Tenon accessibility/CMS products.
- The current PyPI distribution, `tenonhq`, is effectively the competitor's domain. Publishing
  under it invites brand confusion and a possible trademark complaint; trademark use is
  jurisdiction-specific and needs counsel.
- The GitHub repository can stay `haqaliz/tenon`, but the **product, PyPI name and launch name**
  should not be the colliding ones.

## Recommendation

**Blocker: decide the launch name before submitting to Product Hunt.** Pick a distinct name and
re-check the same surfaces for it (PyPI, npm, GitHub org/repo, `.com`/`.dev`, Product Hunt). If the
decision is to keep `Tenon`, get legal advice first and make the differentiation explicit
(“Tenon — API migration PRs”), but the domain/package collision remains.

Until the decision, this kit uses **Tenon** as the working name; every launch asset must be updated
when the name changes. The PyPI trusted-publisher setup in `docs/RELEASE.md` uses `tenonhq` today
and must be changed with the name.
