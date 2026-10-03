# Product Decisions and Open Questions

Updated 2026-10-02. This is the durable brainstorming record; PRODUCT_VISION and LAUNCH_CRITERIA are the implementation/review contracts.

## Confirmed owner requirements
- Somatic practice companion to an existing reflection/identity-building app.
- Teach practical self-management, self-trust, self-authorship, and social discernment, informed by the owner's lived experience.
- Return authority to the person; avoid dependency on app or creator.
- Guide people toward what may help instead of requiring them to pick unfamiliar exercises.
- Body awareness in service of wants/needs is one experience, not the app's entire positioning.
- Include an experience addressing scattered thoughts, overwhelm, and rising panic, professionally framed.
- Add user login.
- Require explicit acceptance of Terms & Conditions (AGB) as part of entering authenticated use. “Sign” is recorded as an explicit acceptance requirement; no handwritten or qualified electronic signature mechanism has been specified.
- Require the user to select a supported language. Apply it throughout the app.
- Develop for European markets first, with English included.

## Open implementation decisions — do not silently assume approval
- Exact initial countries and languages. Europe-first does not identify a finite locale list; English is confirmed, German is a candidate, not yet explicitly approved.
- Login method/provider, account recovery, whether guest previews exist, and what personal data an account stores.
- Final app branding: FeelAnything / FeelY / existing Eso1 prototype.
- Legal entity, applicable legal scope, reviewed Terms/Privacy texts and their translations; acceptance versioning and re-acceptance policy.
- Reviewed sources and detailed content for the initial practice library.

## Superseded assumptions
- The three esoteric prototype experiences are not mandatory product features.
- The earlier no-account scope is superseded by the owner's explicit login requirement.
- The owner need not provide an exercise protocol before the team can design guided entry and research practice content.

## Automation status
The bounded infrastructure trial implemented navigation state restoration, then stopped on a failed Gradle gate. The automated Claude → Codex → Claude cycle has NOT yet completed. App changes are preserved for diagnosis. No launch or publication is authorized by this brainstorming record.
