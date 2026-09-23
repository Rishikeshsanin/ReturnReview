# Final Screenshot Checklist

Capture these only after the real CV/LLM artifacts are active.

## Required product screenshots

1. **Dashboard**
   - ReturnReview branding
   - recent cases
   - truthful readiness state

2. **Create case**
   - product/category
   - customer reason
   - clean responsive form

3. **Multi-image evidence**
   - 2–4 uploaded views
   - image-quality labels/warnings

4. **CV evidence**
   - original image
   - segmentation overlay
   - category verification score
   - defect label/confidence
   - visible affected area

5. **AI review**
   - structured summary
   - evidence-image references
   - policy citation
   - uncertainties

6. **Human review**
   - edited summary/notes
   - approve/reject/request-more-evidence controls

7. **Audit timeline**
   - chronological evidence of processing/reviewer actions

8. **Evaluation**
   - only real generated held-out metrics

## Evidence screenshots for report appendix

- GitHub CI all green
- Railway API/web healthy
- Supabase `return_review` schema/table list without exposing secrets
- architecture diagram
- confusion matrix / mask examples generated from held-out evaluation

## Do not include

- API keys
- database passwords/connection strings
- Supabase secret/service-role keys
- fake metrics
- training-set examples labelled as held-out results
- personally identifiable test data
