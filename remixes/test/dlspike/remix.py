"""Demand-load spike: MODULATION loaded on demand (Remix.window_demand), beside the stock effects.

A port-only instrument (docs/proposals/DEMAND_LOAD.md): MODULATION's id dispatches to a stub that is dry until DLCOPY
has published the code, which DLPUMP stages when a track uses MODULATION. DLWRAP fronts PLATE REV."""
from remix.schema import Proof, Remix
REMIX = Remix(family="effects", proof=Proof.CHECK, proof_note="",
              name="dlspike", doc="Demand-load spike: MODULATION loaded on demand.",
              modules=("USB", "LOAD METER", "DLPUMP", "DLCOPY", "MODULATION", "DLWRAP",
                       "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER", "CHORUS", "SPATIALIZER",
                       "COMB FILTER", "COMPRESSOR", "LO-FI", "DELAY", "SPRING REV", "PLATE REV"),
              fx1=("MODULATION", "DLWRAP", "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER", "CHORUS",
                   "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI"),
              window=(("DLCOPY", 0x33DA3), ("DLWRAP", 0x33F40), ("MODULATION", 0x35000)),
              window_demand=(("MODULATION", 0x33E60),),
              fallback="NONE",
              settings={("octabam.usb", "TRACKS"): "PRE", ("octabam.usb", "MAIN"): 0,
                        ("octabam.usb", "CUE"): 0, ("octabam.usb", "MASTER"): 0,
                        ("octabam.usb", "IN"): "OFF"})
