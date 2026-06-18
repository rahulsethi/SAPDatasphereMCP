# Commercial Licensing

Starting with **v1.0.0**, SAP Datasphere MCP Server is distributed under the
[Business Source License 1.1](https://mariadb.com/bsl11/) (BSL 1.1).
Versions **v0.3.1 and earlier remain MIT-licensed** and unaffected.

BSL 1.1 allows free use for personal, research, academic, and internal
evaluation purposes. **Commercial use requires a separate commercial license**
from the maintainer. On **2029-01-01** the code automatically converts to
Apache 2.0 — permanently and irrevocably free.

## TL;DR

| Use case | License needed |
|---|---|
| Personal experimentation, hobby projects | BSL (free) |
| Academic research / teaching | BSL (free) |
| Time-bounded enterprise evaluation / POC | BSL (free) |
| Paid consulting using the server | **Commercial** |
| Embedding in a vendor product | **Commercial** |
| Hosted SaaS / managed offering | **Commercial** |

## Getting a commercial license

Open a [GitHub Discussion](https://github.com/rahulsethi/SAPDatasphereMCP/discussions)
with the title pattern `[Commercial License Inquiry] <your-org>` and include:

- Company name
- Intended use (consulting, embed, SaaS, internal production)
- Deployment scale (single-tenant, multi-tenant, customer-facing)

Typical response time: 5 business days. Pricing is bespoke and simple — no
per-tool or per-seat counting. A 2-for-1 family discount is available if you
also need a commercial license for the sibling
[SAPBDCMCP](https://github.com/rahulsethi/SAPBDCMCP) repo.

## Activating your commercial license

Once a commercial license is issued, set the provided key in your environment:

```bash
export DATASPHERE_LICENSE_KEY="DS-XXXX-XXXX-XXXX"
```

The server logs a confirmation line on startup:

```json
{"event":"commercial_license_active","key_prefix":"DS-XXXX","v":"1.0.0"}
```

This key is used for your own records and support conversations — it does not
gate features or require network validation.

## Contributing

Contributing code does **not** require a commercial license. Community PRs are
accepted under the BSL 1.1 license. Contributors retain copyright
(no CLA required at v1.0).
