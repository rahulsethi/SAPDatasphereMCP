# Commercial Licensing

SAP Datasphere MCP Server is free for personal, research, and non-commercial use under the **PolyForm Noncommercial 1.0.0** license. Commercial use requires a separate, friendly, low-friction commercial license. This document explains the boundary, what counts as which, and how to obtain a commercial license without a lawyer call.

See also: [MIGRATION.md](./MIGRATION.md) · [SAP_API_POLICY.md](./SAP_API_POLICY.md)

---

## 1. Default license

v1.0 and onward ship under the **[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/)** license.

PolyForm Noncommercial is a modern, short, plain-English source-available license that grants broad rights for **personal use, research, evaluation, and any non-commercial deployment**. You can read, modify, redistribute, and run the code — including inside companies — as long as the use itself is not commercial. The license is widely used by mature open-source projects with a paid commercial tier (e.g., Sentry's BSL-derived stack, several developer-tools companies); it is not a homegrown license.

**What PolyForm Noncommercial allows:**

- Personal use on your own machine.
- Academic research, coursework, and teaching.
- Hobby projects, side experiments, internal R&D.
- **Internal enterprise evaluation or POC** at a company, with a reasonable time-bounded evaluation period.
- Community contributions and forks.
- Embedding inside other non-commercial projects.

**What PolyForm Noncommercial does not allow:**

- Using the server commercially in a paying engagement.
- Embedding the server inside a commercial product you ship or license to customers.
- Running the server as part of a paid SaaS, managed service, or hosted offering.
- Reselling, sublicensing, or white-labeling the server as part of a paid arrangement.

If you are doing any of the second list, you need a commercial license — and we want to make that easy.

---

## 2. What counts as "commercial"

The short list:

- **Paid consulting or professional services** that use this server as part of the delivered work — e.g., a consultant running it against a customer's tenant during a billable engagement.
- **Embedding in a vendor product** — the server (or any non-trivial portion of it) is included in software your company sells, licenses, or rents to customers.
- **Hosted SaaS or managed service** — the server is part of a paid offering your company runs on behalf of others.
- **Internal commercial operations** — using the server as a load-bearing piece of a revenue-generating workflow inside your company that has moved past the evaluation stage.

If your use produces revenue (directly or indirectly, immediately or eventually), and it is not pre-purchase evaluation, assume it is commercial and reach out.

---

## 3. What counts as "noncommercial"

The short list:

- **Personal exploration** — you, on your laptop, learning Datasphere or MCP.
- **Academic research** — universities, students, research labs.
- **Hobby projects, conference demos, blog post examples.**
- **Internal evaluation / POC at an enterprise** — your team is trying the server against a dev or test tenant to decide whether to standardize on it. A reasonable, time-bounded evaluation period (say, up to 90 days) is fine without a commercial license; if the answer is "yes, we're going to depend on this," that is when the commercial conversation starts.
- **Open-source community contributions** — see Section 8.

When in doubt, ask. The penalty for asking and being told "you don't need a license for that" is zero. The penalty for assuming the wrong way is awkward.

---

## 4. Getting a commercial license

We have intentionally designed this path to be **friendly, fast, and lawyer-light**.

**Preferred path — open a GitHub Discussion:**

1. Go to [github.com/rahulsethi/SAPDatasphereMCP/discussions](https://github.com/rahulsethi/SAPDatasphereMCP/discussions).
2. Open a new discussion with the title pattern:

   ```text
   [Commercial License Inquiry] <your-org>
   ```

3. In the body, briefly mention:
   - Company / organization name
   - Intended use (one or two sentences — paid consulting, embedded product, hosted service, internal production, etc.)
   - Deployment scale (single-tenant / multi-tenant / customer-facing / number of seats or end users, if known)
   - Timeline (rough)

**Alternative — email the maintainer:**

`<contact@your-org-here>` *(maintainer: replace this placeholder with your real contact email before publishing this file)*

Either path is fine. The Discussion path is preferred only because it keeps a public record that other prospective commercial users can see, which tends to accelerate the conversation for everyone.

**Response SLA:** we aim to reply within **5 business days**. Most inquiries get a same-week answer.

---

## 5. Pricing approach

Pricing is **bespoke**, based on intended use and deployment scale, but the underlying philosophy is **simple**:

- **No per-tool counting.** You get the whole tool surface.
- **No per-seat or per-user counting** for typical enterprise deployments. We are not in the business of policing how many of your data engineers open Claude Desktop.
- **Flat annual fee** is the default structure for most enterprise deployments.
- **Tiered pricing** for vendors embedding the server in a product they sell — based on the number of customers your product serves.
- **Startup-friendly terms** for early-stage companies — we will work with you.

We prefer simplicity. If you tell us your use case, you will get a single number, not a 12-row pricing matrix.

---

## 6. Pre-1.0 versions

**v0.3.1 and all earlier releases are MIT-licensed and unaffected by this change.** The PolyForm Noncommercial 1.0.0 license governs only the **v1.0 and later** codebase. Commercial users currently on v0.3.x are not retroactively required to obtain a commercial license — your MIT-licensed copy remains MIT-licensed.

That said, we strongly recommend upgrading:

- The **SAP API path migration** (`/api/v1/dwc/*` → `/api/v1/datasphere/*`) is in v1.0; the legacy path tree disappears in **March 2027**.
- The **governance posture** (audit log, redaction layer, policy gate, MCP tool annotations) ships only in v1.0+ and is what enterprise reviewers will look for.
- The **MCP Prompts, Resources, and structured outputs** are v1.0+ only.

If you are a commercial user evaluating the upgrade and want to discuss licensing as part of the upgrade decision, the GitHub Discussion path above is exactly the right channel — we are happy to talk through the trade-offs.

---

## 7. Sibling product

The same commercial license arrangement applies to **[SAPBDCMCP](https://github.com/rahulsethi/SAPBDCMCP)**, the SAP Business Data Cloud MCP server, on the same terms. Same maintainer, same naming conventions, same license model.

If your use case spans both Datasphere and BDC — which is increasingly common, given that Business Data Cloud is now the umbrella product family for both — a **2-for-1 family discount** is available on request. Mention "both products" or "family discount" in your inquiry and we will quote accordingly.

---

## 8. Open source contributions

**Contributing code to this project does not require a commercial license.** We welcome community pull requests under the PolyForm Noncommercial license. There is **no Contributor License Agreement (CLA)** at v1.0 — contributors retain copyright over their own contributions and license them inbound under PolyForm Noncommercial.

If you are unsure whether a contribution would be welcome before investing time, open a GitHub Discussion first — we are happy to talk through proposed changes early.

For the avoidance of doubt:

- You can contribute to the project even if your day job involves commercial use of SAP products.
- You can contribute even if your employer is itself a potential commercial-license customer.
- The "commercial vs. noncommercial" boundary is about **how the running software is used**, not **who contributed the code**.

---

If you got to the bottom of this page and you still are not sure which category you fall into, open a Discussion and ask. Five minutes of conversation beats five hours of guessing.
