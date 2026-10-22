# EDIT EVENTS

Platform owner of held-step encoder dispatch and the native pattern/track copy
sites shared by extended editors. It adds no controls or retained storage.

Register `(module key, symbol prefix, events)` in `CLIENTS` in `manifest.py`,
following STORE. Only selected clients enter the generated tables; unresolved
handlers fail linking. Declare `requires=('EDIT EVENTS',)` and select the module.

| Event | Contract |
| --- | --- |
| held | `<prefix>_claim(d0=encoder, d1=delta)` returns zero to pass; nonzero selects `<prefix>_handle` with the original native entry frame |
| copy_pre | d0=destination, d1=source, d2=length; before native data moves |

Held predicates must be read-only. Registration order is explicit precedence:
the first matching predicate wins. A new editor must declare its exact context
and test overlap and fallthrough with existing editors. Handlers return as the
native held editor would; they must not re-enter this dispatch. No owner means
one native fallback. This supports multiple editors on the same track type.

Copy notifications visit every client in registration order. Each client owns
its side data and filters addresses/lengths for its supported objects. Native
memcpy executes once after the notifications, and its result is returned unchanged.
Callbacks may clobber d0–d7/a0–a6; preserve SP and interrupt mask. Dispatcher
frames are stack-local. Client scratch state may impose stronger non-reentrancy.

The copy sites include pattern/track clipboard and undo transfers. This does
not pretend every clear/paste command is memcpy: distinct MIDI/audio trig-clear
and trig-paste hooks remain in their owning modules. Project/Part persistence
belongs to STORE. Add further shared editing boundaries here only after auditing
the native ABI and before/after semantics, with behavior tests at installed hooks.

PLOCKS P2's pre client preserves FX page-two locks and claims held audio FX SETUP edits. The dispatcher has no knowledge of its data format.


## Verification and cost

`tools/verify/verify_edit_events.py` assembles this source with zero, one and
three unrelated synthetic clients. It checks first-owner precedence (including
overlapping claims), native fallthrough, original arguments, registers and stack,
condition codes, callback order, and exactly one native copy. Synthetic clients
clobber all permitted registers and condition codes; the native copy and client
bodies are substituted at their entry points. This is dispatcher evidence, not
an emulation of the complete editor.

The same test counts executed dispatcher instructions, excluding client bodies
and the native copy body. For zero/one/three clients registered for every event,
copy dispatch takes 29/37/53 instructions; held fallthrough takes 16/28/52,
including its two displaced native instructions but excluding the entry jump.
These are instruction counts, not cycle counts or physical latency measurements.

Only `held` and `copy_pre` are exposed: both have PLOCKS as a client. Future
editing boundaries belong with the first module that consumes them, together
with a native ABI audit and installed-image behavior tests. The dispatcher does
not run on sequencer notes.

`tools/verify/verify_edit_event_clients.py` checks the built image's 21 installed
hooks and three executable PLOCKS callbacks. `tools/verify/verify_plocks_p2.py`
then exercises the real editor, copying, playback, panel display and persistence
on a disposable project under the port. The selection/claims ledger refuses
other modules that independently patch the same sites. Predicates must pass
outside their exact context; one selected handler or one native fallthrough is
the guard against processing an edit twice.

Hardware acceptance of this migration remains open. Software checks cannot
establish physical panel timing, interrupt interleaving or live audio behavior.
Relevant hardware configurations are FX1 and FX2 edits, multiple held steps,
multiple audio tracks, native MIDI/page-one fallthrough, copy/paste/clear/undo,
and editing during playback. Earlier PLOCKS hardware reports predate this
shared dispatcher and do not qualify it.
