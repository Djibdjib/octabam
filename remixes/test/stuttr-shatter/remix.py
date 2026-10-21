"""SHATTER + STUTTR + stock — refused by Module.conflicts (stall bisect).

Exists so the ledger refuse is checkable: `make bus REMIX=stuttr-shatter`
must fail with the declared SHATTER conflict. HW S8 (latest+both) stalls
empty play; pair+stock alone still open (see modules/stuttr/README.md).
"""
from remix.schema import Proof, Remix

REMIX = Remix(
    name="stuttr-shatter",
    family="effects",
    proof=Proof.CHECK,
    proof_note="build must refuse: STUTTR conflicts SHATTER (HW S8 stall)",
    doc="Refused pair: SHATTER + STUTTR beside stock (PLATE+SPRING harvested).",
    modules=(
        "SHATTER",
        "STUTTR",
        "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER",
        "CHORUS", "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI",
        "DELAY", "DARK REV",
    ),
    fallback="NONE",
)
