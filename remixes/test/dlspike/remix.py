"""Demand-load spike: MODULATION's code at P:0x35000 and DLSTUB in front of it, beside the stock effects.

A port-only instrument (modules/dlstub/README.md): the stub on id 0x1b is dry until its shared words say the code at
P:0x35000 is resident. MODULATION (id 0x0e) is also placed, as the reference the stub's output is compared with."""
from remix.schema import Proof, Remix
REMIX = Remix(family="effects", proof=Proof.CHECK, proof_note="",
              name="dlspike", doc="Demand-load spike: DLSTUB in front of MODULATION's window code.",
              modules=("USB", "MODULATION", "DLSTUB", "DLWRAP",
                       "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER", "CHORUS", "SPATIALIZER",
                       "COMB FILTER", "COMPRESSOR", "LO-FI", "DELAY", "SPRING REV", "PLATE REV"),
              fx1=("MODULATION", "DLSTUB", "DLWRAP", "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER", "CHORUS",
                   "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI"),
              window=(("DLSTUB", 0x33DA3), ("DLWRAP", 0x33E80), ("MODULATION", 0x35000)),
              window_demand=("MODULATION",),
              fallback="NONE",
              settings={("octabam.usb", "TRACKS"): "PRE", ("octabam.usb", "MAIN"): 0,
                        ("octabam.usb", "CUE"): 0, ("octabam.usb", "MASTER"): 0,
                        ("octabam.usb", "IN"): "OFF"})
