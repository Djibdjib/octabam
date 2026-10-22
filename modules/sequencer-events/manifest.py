"""Shared native sequencer boundaries; clients own their musical policies."""
from remix.schema import Category, Detour, Gate, Kind, Linked, Module, Proof

EVENTS = ('start', 'resume', 'midi_note_accepted')
# Build-time registration, following STORE. Tuple order is callback order.
# No handler may emit MIDI or re-enter the sequencer from these notifications.
CLIENTS = (
    ('EUCLID', 'eu_seq', ('start', 'resume')),
)

def event_inc(modules, remix=None):
    out = []
    seen = set()
    for key, prefix, handled in CLIENTS:
        if key in seen or len(set(handled)) != len(handled) or set(handled) - set(EVENTS):
            raise ValueError(f'invalid SEQUENCER EVENTS registration: {key}')
        seen.add(key)
    for event in EVENTS:
        out.append(f'seq_ev_{event}:')
        for key, prefix, handled in CLIENTS:
            if key in modules and event in handled:
                out.append(f'    .long {prefix}_{event}')
        out.append('    .long 0')
    return '\n'.join(out) + '\n'

MODULE = Module(
    name='sequencer-events', key='SEQUENCER EVENTS', kind=Kind.CF_PATCH,
    category=Category.PARTS, author='radiohagen',
    author_url='https://github.com/radiohagen', proof=Proof.CHECK,
    proof_note='Assembled dispatcher tests (0/1/3 clients), native MIDI and installed-hook checks; empty MIDI path adds 34 instructions. MKII owner checks: EUCLID transport configurations (21 Oct 2026); corrected EUCL EVENTS 98 ordinary/arpeggiated MIDI start, resume and clean stop (22 Oct 2026). Callback payloads and multiple clients remain software-tested ([PR #851](https://github.com/sambanks/octabam/pull/851)).',
    doc='Platform: shared transport and accepted MIDI-output notifications.',
    linked=(Linked('sequencerevents', 'modules/sequencer-events/events.s', dram=True, include=event_inc),),
    gates=(Gate('tools/verify/verify_system_events.py', once=True, venv=True),
           Gate('tools/verify/verify_event_clients.py', stage='image', venv=True)),
    detours=(
        Detour(0x4009c3d4, bytes.fromhex('23c0800065b8'), 'sequencerevents', 'seq_start', 'transport start'),
        Detour(0x4009c4d4, bytes.fromhex('23c0800065b8'), 'sequencerevents', 'seq_resume', 'transport resume'),
        Detour(0x4009fbb2, bytes.fromhex('7339400d807c'), 'sequencerevents', 'seq_sent_a', 'accepted MIDI output'),
        Detour(0x4009fcfa, bytes.fromhex('7139400d807c'), 'sequencerevents', 'seq_sent_b', 'accepted MIDI ownership replacement'),
    ),
)
