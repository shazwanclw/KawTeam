# Supplier history and navigation motion

Keep the stationary hamburger, with three lines animating to a close shape as the sidebar opens. Blend its background into the sidebar and use matching timing; respect reduced-motion preferences.

Add a separate history icon beside each approval/secured supplier row. Open an accessible dialog showing saved sent and received messages for only this supplier and task in chronological order. Show timestamps, subjects, sender direction and bodies as plain text. Preserve older task revisions as labelled history and clearly mark demo records. Never fabricate missing messages or fetch an unrelated inbox. Empty history explains that no messages have been recorded.

Verify supplier isolation, ordering, separate row/history actions, empty history, fixed toggle position, animated icon and reduced-motion behavior with mocked browser checks. Run frontend tests, TypeScript and lint.

Implemented and reviewed. Verification: 45 frontend tests, TypeScript and ESLint passed; isolated browser checks confirm ordered supplier-only history, empty state, separate approval action, focus restoration, fixed animated toggle, reduced motion and mobile width. Every gateway call was mocked; no supplier emails were sent.
