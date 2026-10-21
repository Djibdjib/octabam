"""Build a private, deterministic audio project for hardware regressions.

Source files are read only. Generated Octatrack files stay outside Git.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import toolpath
import ab_fixture
import stress_project
from hw import ot_project as otp, ot_bank as bank
from remix import registry


def prepare(source, destination, remix, effects, patterns):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.exists():
        raise ValueError(f'Output already exists: {destination}; choose a fresh directory')
    if source == destination or source in destination.parents:
        raise ValueError('Output must be separate from the source project')
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in source.iterdir() if p.is_file()}
    ab_fixture.prepare(source, destination)
    stress_project.set_project_text(destination)
    stress_project.set_markers(destination)
    sample = destination / stress_project.SAMPLE_REL
    stress_project.make_sample(sample)
    for p in destination.glob('project.*'):
        data = p.read_bytes()
        blocks = re.findall(rb'\[SAMPLE\].*?\[/SAMPLE\]\r?\n', data, re.S)
        only = next(b for b in blocks if b'TYPE=FLEX\r\nSLOT=001\r\n' in b)
        data = re.sub(rb'\[SAMPLE\].*?\[/SAMPLE\]\r?\n', b'', data, flags=re.S)
        p.write_bytes(data.rstrip() + b'\r\n\r\n' + only + b'\r\n')
    modules = registry.modules()
    for path in sorted(destination.glob('bank*.work')):
        number = int(path.stem[4:])
        def mutate(data):
            for part in range(otp.NPARTS_ALL):
                base = otp.PART_BASE + part * otp.PART_STRIDE
                for track in range(8):
                    data[base + otp.SLOT_OFF + track * 5 + 1] = 0
                    data[base + 0x01b + track * 2] = 80
                    setup = base + 0x1e3 + track * 30 + 6
                    values = base + 0x033 + track * 30 + 6
                    data[setup] = 1
                    data[setup + 4] = 0
                    data[values:values + 6] = bytes((64, 0, 127, 127, 0, 0))
                    for scene in range(16):
                        at = base + 0x66b + (scene * 8 + track) * 32
                        data[at:at + 30] = b'\xff' * 30
                for slot, track, key, overrides in effects:
                    module = modules[key]
                    values = otp.module_defaults(module, overrides)
                    sub = 0 if slot == 'fx1' else 6
                    idoff = otp.FX1_OFF if slot == 'fx1' else otp.FX2_OFF
                    data[base + idoff + track - 1] = module.menu.fx2_id
                    p1 = base + otp.P1_OFF + (track - 1) * otp.TRACK_STRIDE + sub
                    p2 = base + otp.P2_OFF + (track - 1) * otp.P2_STRIDE + sub
                    data[p1:p1 + 6], data[p2:p2 + 6] = values[:6], values[6:]
            for pat in range(16):
                tail = bank.PTRN_BASE + pat * bank.PTRN_STRIDE + bank.PTRN_STRIDE - 11
                data[tail + 2:tail + 4] = bytes((16, 2))
                data[tail + 6] = 0  # all patterns use Part 1
                for track in range(8):
                    at = otp.trac_off(pat, track)
                    data[at:at + 64] = bytes(64)
                    data[at + 0x50:at + 0x52] = bytes((16, 2))
                    data[at + 0x59:at + 0x59 + 64 * 32] = b'\xff' * (64 * 32)
                    # No inherited MIDI trigs in a hardware audio fixture.
                    midi = bank.PTRN_BASE + pat * bank.PTRN_STRIDE + 8 + 8 * 0x922 + track * 0x8b9
                    assert data[midi:midi + 4] == b'MTRA'
                    data[midi + 9:midi + 9 + 64] = bytes(64)
                if number == 1:
                    for track, steps in patterns.get(pat + 1, {}).items():
                        for step in steps:
                            at = otp.trac_off(pat, track - 1)
                            data[at + 7 - (step - 1) // 8] |= 1 << ((step - 1) % 8)
        otp._bank_write(destination, number, mutate, guard=False)
    otp.write_stored(destination)
    for path in destination.glob('bank*.work'):
        data = path.read_bytes(); bank.check_tags(data)
        assert int.from_bytes(data[-2:], 'big') == sum(data[0x10:-2]) & 0xffff
        for pat in range(16):
            for track in range(8):
                expected = patterns.get(pat + 1, {}).get(track + 1, ()) if path.name == 'bank01.work' else ()
                assert bank.trigs(data, pat, track) == [s - 1 for s in expected]
                assert not bank.locks(data, pat, track)
    assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in source.iterdir() if p.is_file()}, 'Source changed'
    files = {str(p.relative_to(destination)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(destination.rglob('*')) if p.is_file()}
    receipt = dict(source=str(source), source_unchanged=True, remix=remix,
                   effects=effects, patterns=patterns, sample_format='44100 Hz, stereo, 16-bit PCM',
                   files=files, hardware_status='not run')
    (destination / 'fixture.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return destination
