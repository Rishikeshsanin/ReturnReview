# Security and Data-Safety Notes

- Secrets remain server-side and are loaded from environment variables.
- `.env` files, local databases, model checkpoints and uploaded images are gitignored.
- Uploads accept only JPEG/PNG/WebP, enforce a size limit, verify image decoding, normalize EXIF orientation and generate unique storage names.
- Unexpected exceptions are logged server-side; raw stack traces are not returned to users.
- Request IDs allow failures to be correlated without logging API keys.
- LLM tools are read-only. Database writes and reviewer decisions are deterministic backend operations.
- The LLM is not permitted to infer fraud, intent, authenticity, invisible/internal damage, causality or responsibility.
- A deterministic grounding guard checks evidence IDs, supported defect classes and retrieved policy references.
- Supabase is **not connected yet**. Because the user's Supabase environment is shared by unrelated projects, ReturnReview will not create/alter tables, policies, buckets or data until the Project Hub Supabase README and existing schema are inspected read-only.
- No unrelated repository or data source is part of this project.
