/** Reveal a labelled field without losing the user's draft or other disclosure state. */
export function revealInvalidField(root: HTMLElement, label: string) {
  const field = Array.from(root.querySelectorAll<HTMLElement>('input, select, textarea'))
    .find(element => element.getAttribute('aria-label') === label)
  if (!field) return
  for (let parent = field.parentElement; parent && parent !== root; parent = parent.parentElement) {
    if (parent.tagName === 'DETAILS') (parent as HTMLDetailsElement).open = true
  }
  field.setAttribute('aria-invalid', 'true')
  field.setAttribute('aria-describedby', 'scenario-error')
  field.focus()
}
