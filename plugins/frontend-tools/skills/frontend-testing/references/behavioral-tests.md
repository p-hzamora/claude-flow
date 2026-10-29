# Behavioral frontend tests

Use unit tests for pure validation and transitions, component integration tests for
interactions and provider wiring, and browser tests for critical cross-screen journeys.
Do not force a coverage percentage or mock every child component. Favor regressions
that could fail even if internal implementation changes completely.

Query by role and accessible name, then labels/text as appropriate; use test IDs for
cases without a meaningful semantic query. Simulate interaction with a per-test
`userEvent.setup()` instance and await its actions. Use `findBy*` for eventual presence,
`queryBy*` for absence, and `waitFor` for assertions that must eventually hold. Do not
put clicks or submissions in waitFor callbacks; retries would repeat side effects.

```tsx
// Assumes the project's runner, DOM environment, and jest-dom matchers are configured.
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test } from 'vitest';
import { RenameForm } from './RenameForm';

test('submits the name entered by the user', async (): Promise<void> => {
  const user: ReturnType<typeof userEvent.setup> = userEvent.setup();
  const saved: string[] = [];
  render(<RenameForm onSave={async (name): Promise<void> => { saved.push(name); }} />);
  await user.type(screen.getByRole('textbox', { name: 'Name' }), 'Ada');
  await user.click(screen.getByRole('button', { name: 'Save' }));
  expect(await screen.findByRole('status')).toHaveTextContent('Saved');
  expect(saved).toEqual(['Ada']);
});
```

The example defines an illustrative component contract, not an importable fixture.
Use the actual runner's imports and setup in real tests. Assert what the user observes
and what crosses a meaningful boundary, not component state or Hook call counts.

For a network-backed feature, intercept at the network boundary using existing mocking
tools, or inject a narrow API seam when that is already part of the design. Exercise
pending, rejected, empty, and successful responses as relevant. Test retry and stale
response behavior when the changed code owns them. Avoid arbitrary timeouts; control
promise resolution or the runner's clock where timing is the behavior being tested.

Create fresh providers/query clients per test when caches could leak. Reset handlers,
restore mocks and real timers, and clean up subscriptions. Use fake timers deliberately;
configure user-event timer advancement according to the installed runner. Do not mask
act warnings with blanket wrappers or assertions that only pass after fixed delays.

Check label/error associations and meaningful status announcements. Simulated DOM
cannot reliably verify CSS visibility, layout, full tab/focus behavior, or assistive
technology output. Complement it with actual keyboard/browser checks for changed
complex interactions. A snapshot or automated accessibility scan is supporting evidence,
not proof of usability or full conformance.
