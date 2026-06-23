# Finance Tracker Frontend

React/Vite frontend for the Finance Tracker app.

## Mock Feature Capture Notes

These notes describe capture ideas for the current frontend mockups. They are not backend implementation yet.

### Savings Goals

- Avoid automatic savings detection because the app cannot know whether money was saved in cash, a locked account, M-Pesa, SACCO, or elsewhere.
- Start with manual tagging: user marks a transaction as contributing to a goal.
- Later bot flow: if the user has daily budget surplus, the bot can ask whether to add that surplus to a chosen goal.

### Bills & Subscriptions

- Start with manual setup: name, amount, billing cycle, and due date.
- The bills list should stay sorted from soonest due to farthest due.
- Later parsing idea: detect repeated transactions and suggest a recurring bill, but require user confirmation.

### Quotations

- Start with manual quote entry: item, quantity, supplier, and unit price.
- Comparisons should work only when quotation item lists match.
- Later AI idea: read a photo/PDF quote and suggest structured items for review before saving.
