
''' Hardware details for the Intel Ivy Bridge microarchitecture. '''

# Types of floating-point operation with their cost in cycles
# (from http://www.agner.org/optimize/instruction_tables.pdf).
# Operations are in order of decreasing cost (for use when
# searching for duplicated sub-graphs).
# TODO these costs are microarchitecture specific.
OPERATORS = {"/":14, "+":1, "-":1, "*":1, "FMA":1}

# Size of a cache line in bytes
CACHE_LINE_BYTES = 64

# Clock speed to use when computing example performance figures
EXAMPLE_CLOCK_GHZ = 3.8

# Fortran intrinsics that we recognise, with their cost in cycles
# (as obtained from micro-benchmarks: dl_microbench).
# TODO these costs are microarchitecture (and compiler+flags) specific.
FORTRAN_INTRINSICS = {"SIGN":3, "SIN":49, "COS":49}

# Whether this microarchitecture supports the Fused Multiply Add op
# TODO check on this before we attempt to generate FMAs.
SUPPORTS_FMA = False
