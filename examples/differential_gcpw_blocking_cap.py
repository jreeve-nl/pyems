#!/usr/bin/env python3

import os
import sys
import numpy as np
from pyems.simulation import Simulation
from pyems.pcb import common_pcbs
from pyems.structure import (
    DifferentialMicrostrip,
    PCB,
    common_smd_passives,
    SMDPassive,
)
from pyems.coordinate import Coordinate2, Axis, Box3, Coordinate3
from pyems.utilities import print_table, mil_to_mm
from pyems.field_dump import FieldDump, DumpType
from pyems.mesh import Mesh

freq = np.arange(4e9, 18e9, 10e6)
unit = 1e-3
ref_freq = 5.6e9
sim = Simulation(freq=freq, unit=unit, reference_frequency=ref_freq)

pcb_len = 30
pcb_width = 10

trace_width = 0.85
gnd_gap = mil_to_mm(6)
trace_gap = mil_to_mm(6)

cap_dim = common_smd_passives["0402C"]
cap_dim.set_unit(unit)
pad_length = 0.6
pad_width = trace_width

pcb_prop = common_pcbs["oshpark4"]
pcb = PCB(
    sim=sim,
    pcb_prop=pcb_prop,
    length=pcb_len,
    width=pcb_width,
    layers=range(3),
)

DifferentialMicrostrip(
    pcb=pcb,
    position=Coordinate2(
        (-pcb_len / 2 - cap_dim.length / 2 - pad_length / 2) / 2, 0
    ),
    length=pcb_len / 2 - cap_dim.length / 2 - pad_length / 2,
    width=trace_width,
    gap=trace_gap,
    propagation_axis=Axis("x"),
    gnd_gap=(gnd_gap, gnd_gap),
    port_number=1,
    excite=True,
    ref_impedance=50,
)

# values based on Murata GJM1555C1H100FB01 (ESR at 6GHz)
SMDPassive(
    pcb=pcb,
    position=Coordinate2(0, trace_gap / 2 + trace_width / 2),
    axis=Axis("x"),
    dimensions=cap_dim,
    pad_width=pad_width,
    pad_length=pad_length,
    gap=gnd_gap,
    c=10e-12,
)

SMDPassive(
    pcb=pcb,
    position=Coordinate2(0, -trace_gap / 2 - trace_width / 2),
    axis=Axis("x"),
    dimensions=cap_dim,
    pad_width=pad_width,
    pad_length=pad_length,
    gap=gnd_gap,
    c=10e-12,
)

DifferentialMicrostrip(
    pcb=pcb,
    position=Coordinate2(
        (pcb_len / 2 + cap_dim.length / 2 + pad_length / 2) / 2, 0
    ),
    length=pcb_len / 2 - cap_dim.length / 2 - pad_length / 2,
    width=trace_width,
    gap=trace_gap,
    propagation_axis=Axis("x", direction=-1),
    gnd_gap=(gnd_gap, gnd_gap),
    port_number=2,
    ref_impedance=50,
)

mesh = Mesh(
    sim=sim,
    metal_res=1 / 80,
    nonmetal_res=1 / 40,
    smooth=(1.1, 1.5, 1.5),
    min_lines=5,
    expand_bounds=((0, 0), (8, 8), (8, 8)),
)

# mesh.add_line_manual(0, -cap_dim.length / 2)
# mesh.add_line_manual(0, cap_dim.length / 2)

FieldDump(
    sim=sim,
    box=Box3(
        Coordinate3(-pcb_len / 2, -pcb_width / 2, 0),
        Coordinate3(pcb_len / 2, pcb_width / 2, 0),
    ),
    dump_type=DumpType.current_density_time,
)

if os.getenv("_PYEMS_PYTEST"):
    sys.exit(0)


sim.run()
sim.view_field()

print_table(
    data=[sim.freq / 1e9, sim.s_param(1, 1), sim.s_param(2, 1)],
    col_names=["freq", "s11", "s21"],
    prec=[2, 4, 4],
)
