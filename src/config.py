# -----------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2015.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
# -----------------------------------------------------------------------------
# Author R. Ford STFC Daresbury Lab

'''PSyclone configuration file where system wide properties and
defaults are set.'''

SUPPORTEDAPIS = ["gunghoproto", "dynamo0.1", "dynamo0.3", "gocean0.1",
                 "gocean1.0"]
DEFAULTAPI = "dynamo0.3"
SUPPORTEDSTUBAPIS = ["dynamo0.3"]
DEFAULTSTUBAPI = "dynamo0.3"
# The pointwise/infrastructure/intrinsic calls that we support
PSYCLONE_INTRINSICS = ["set_field_scalar", "copy_field", "minus_fields", "axpy"]
# Dictionary giving the name of the file containing the meta-data
# describing the intrinsics for each supported API
INTRINSIC_DEFINITIONS = {"dynamo0.3": "dynamo0p3_intrinsics_mod.f90"}
DISTRIBUTED_MEMORY = True
