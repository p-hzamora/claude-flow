# Component contracts and accessible interaction

Prefer composition through children and explicit slots over inheritance or a large
matrix of mode flags. A component should express one coherent UI responsibility, not
necessarily one DOM element. Custom Hooks share stateful behavior, not one shared
state instance across callers. Keep hooks focused on a meaningful interaction.

For TypeScript, `.tsx` holds JSX. Follow `typescript-syntax` typing rules: contextual inline event parameters are an
explicit exception; annotate extracted handlers
with the relevant React event and element type. Use `ReactNode` for renderable slots,
not for every data prop. Native control wrappers can derive props with
`ComponentPropsWithoutRef<'button'>`; preserve native semantics and expose ref support
only according to the installed React version. Avoid an unconditional ref-forwarding
recipe across React versions. Choose controlled or uncontrolled inputs intentionally;
do not switch between them or accept competing default/current values ambiguously.

Use native buttons for actions and anchors for navigation. Give every form control an
associated label; placeholders are not labels. Group related controls with fieldset
and legend where appropriate. Connect instructions and error text to controls, expose
invalid state, and make submission outcomes perceivable. Preserve user input after
failed submission. Set non-submit button types explicitly inside forms.

Keyboard users need reachable controls, visible focus, and a sensible order. For dialogs
and other complex widgets prefer the project's tested accessible primitive; manage
initial focus, escape behavior, and focus restoration. Do not invent a partial ARIA
widget when native HTML suffices. Async status can use a polite live region; avoid
repeated disruptive announcements. Include text or semantics beyond color alone.

Treat raw HTML and URL destinations as trust boundaries. Avoid rendering untrusted
HTML; if required, use the project's maintained sanitizer and explicit policy. Client
validation improves feedback but does not enforce authorization. Browser-exposed build
variables cannot hold secrets. Keep server-only dependencies out of client imports.

Accessibility checks need keyboard and browser verification for focus and layout;
passing automated assertions does not establish complete accessibility conformance.
