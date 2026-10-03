# FeelAnything — Guided Somatic Practice

## Product purpose
This is the somatic practice companion to the owner's existing reflection and identity-building app. It should teach and walk people through practical skills drawn from the owner's lived experience of trauma recovery, self-love, self-management, and self-authorship. It must translate those ideas into concrete, voluntary practice rather than another reflection journal or a collection of esoteric effects.

The owner's clarification on 2026-10-02 supersedes the earlier sensory-ritual brief. Vibrant, Mannequin, and Ascension are existing prototype screens, not mandatory launch features. They may be replaced when an approved practice flow is ready. FeelY appears in the owner's wider concept; the final displayed brand and relationship between products are not yet settled.

## Founding principle
Return authority to the person. Help them gain clarity, make their own choices, and eventually need the app less. Do not position the app or its creator as an authority to obey. Avoid dependency, shame, coercive streaks, diagnostic labels, or claims that every user will reproduce the founder's outcome.

## Intended learning outcomes
- Self-kindness and a sense of worth that do not depend on achievement or approval.
- Noticing bodily experience and choosing a manageable response rather than forcing a particular feeling.
- Self-authorship: choosing a small action even when doubt or shame is present.
- Self-management: recognizing limits, strengths, needs, boundaries, and appropriate support.
- Social discernment: separating observable behavior from interpretation; noticing concerning patterns while allowing uncertainty about another person's intentions.
- Applying these skills in relationships, work, ambition, and leadership without making career success the measure of healing.

The founder's statements about panic, detecting hate, reading intentions, and judging competence are autobiographical source material. Do not turn them into universal truths, infallible detection features, diagnoses, or promises to eliminate panic. The parenting aspiration belongs to the wider vision; child-facing exercises and parenting instruction are outside the first adult practice release.

## Guided entry and practice journey
The app must help people discover a useful starting point. Do not require them to choose a technique, name a body state, or already know what is good for them.

1. Ask a few plain-language questions about the present situation and desired support. Offer approachable answers such as “I feel wound up,” “I feel disconnected,” “Something happened with someone,” “I’m holding myself back,” and “I’m not sure.” These are descriptions, not diagnoses.
2. Ask only follow-up questions that change the recommendation, including available time and preferences such as sound, movement, or remaining seated. Let the user skip or change an answer.
3. Suggest one suitable practice from a reviewed content library. Explain the connection to their answers, what they will actually do, approximate duration, and what it may help them explore. Set realistic expectations before starting; never promise a specific feeling or outcome.
4. Offer a different suggestion or the option to browse. Guidance should reduce the burden of choosing while preserving control.
5. Guide one concrete step at a time with visible pause, skip, alternatives, and exit. Supply enough explanation to understand the purpose of each step without overwhelming the practice.
6. Ask an optional neutral check-in afterward: helpful, no change, uncomfortable, or unsure. Adapt the next suggestion; do not interpret no change as user failure or automatically prescribe a more intense practice.
7. End with an optional small real-world action. Returning is welcome, not a streak obligation. Brief reflection supports practice and does not duplicate the separate identity product.

## Content and recommendation design
The team is responsible for designing this guided experience; the owner is not required to invent a bodily protocol before design work proceeds. The supplied notes establish philosophy and desired skills, not a clinical exercise library.

Design the entry questions, matching rules, explanation cards, session mechanics, and feedback paths. Begin with simple, inspectable recommendation rules and a small curated library rather than an opaque diagnostic score or unconstrained generation of personal treatment. “I’m not sure” must lead to a useful, low-demand starting option, not a dead end.

Before presenting actual practice instructions as ready for users, document each practice’s source, intended use, limitations, alternatives, and exit behavior. Research and review the content appropriately; do not invent trauma-treatment claims or silently relabel the ghost/camera ritual as therapy. The user's lived experience informs tone and goals; it is not evidence that a practice works for everyone.

Clearly distinguish lived-experience teaching from clinical claims. Any future claim of treatment effectiveness or clinical suitability needs appropriate evidence and review before publication. A technical reviewer PASS is not clinical validation. Content requiring specialist review can remain explicitly pending while interaction design and infrastructure progress.

## Experience and design
The experience should feel grounded, warm, clear, respectful, and deliberately designed. Prioritize readable instructions, visible choice, and predictable navigation. Avoid supernatural measurement claims, overstimulating motion, surprise sounds, or obligatory eyes-closed/breath-control interactions. Let the confirmed exercise drive visuals and interaction; do not impose the prototype's visual theme as a product requirement.

Use accessible controls, adaptable type, system insets, and appropriate motion/audio options. Sensitive personal observations should be optional and private. User login is required. Add only the authentication and account infrastructure necessary for the agreed scope; analytics, recording, and unrelated permissions remain out of scope. Persisting personal practice data requires an explicit retention/deletion design.

## Autonomy and boundaries
Agents may substantially redesign or replace prototype code within an explicit current task. Optimize for complete, useful practice rather than feature count. Preserve unrelated work and keep changes reviewable.

Ask the owner for material product/brand decisions, credentials, spending, or publication; do not require the owner to supply a full exercise protocol to continue design. Routine engineering choices are autonomous. Never publish, sign a store release, or treat task completion as launch approval.

## Account, language, and launch market
Develop for European markets first, with English included. The initial European country/language list remains an explicit launch-scope decision; do not assume English-only coverage satisfies Europe-first.

Require a language choice on first use, before language-dependent onboarding or legal acceptance. Device language may suggest a default but must not replace the user's choice. Offer a clearly discoverable language switch and remember the choice across restarts and authenticated sessions. User-selected language takes precedence over the device setting.

Provide user login. Before granting authenticated app access, require explicit, unselected-by-default acceptance of the applicable Terms & Conditions (AGB), with accessible full text in the selected language. Record the accepted version and time against the account; a returning user with valid existing acceptance need not be asked to sign again at every login. Re-acceptance rules for changed terms must be specified. Do not equate acceptance of terms with optional marketing or other separate choices.

Localize the complete user journey: login/recovery, onboarding, guided questions, recommendations, practice content, controls, feedback, errors, accessibility labels, notifications if any, account management, and legal screens. Any shipped audio requires matching language content. Avoid mixed-language fallback in a supported locale; fallback rules for unsupported locales must be deliberate and tested.

See docs/PRODUCT_DECISIONS.md for confirmed requirements/open questions and docs/EXPERIENCE_CATALOG.md for the current experience concepts.
