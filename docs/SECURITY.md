# Security and Data-Safety Notes

- Secrets remain server-side and are loaded from environment variables.
- `.env` files, local databases, model checkpoints and uploaded images are gitignored.
- Uploads accept only JPEG/PNG/WebP, enforce a size limit, verify image decoding, normalize EXIF orientation and generate unique storage names.
- Unexpected exceptions are logged server-side; raw stack traces are not returned to users.
- Request IDs allow failures to be correlated without logging API keys.
- LLM tools are read-only. Database writes and reviewer decisions are deterministic backend operations.
- The LLM is not permitted to infer fraud, intent, authenticity, invisible/internal damage, causality or responsibility.
- A deterministic grounding guard checks evidence IDs, supported defect classes and retrieved policy references.
- Production persistence is the dedicated Railway PostgreSQL service, reached
  only through Railway private networking. The database has no public domain,
  and the API uses the PostgreSQL `public` schema.
- Cases, uploaded image bytes, generated overlays, CV evidence, AI reviews,
  reviewer decisions, and audit events are stored through SQLAlchemy. Database
  writes remain deterministic backend operations.
- The retained Supabase Project Hub foundation is historical and is not the
  production runtime. It must not be modified or removed without a separately
  scoped migration/retirement decision.
- `cv-lightweight-1` artifacts are downloaded during the CV image build and
  checked against the release manifest before the image is accepted. Model
  checkpoints remain gitignored.
- No unrelated repository or data source is part of this project.
