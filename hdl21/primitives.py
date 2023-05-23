"""
# Hdl21 Primitive Modules

Primitives are leaf-level Modules typically defined not by users, 
but by simulation tools or device fabricators. 
Prominent examples include MOS transistors, diodes, resistors, and capacitors. 

Primitives divide in two classes, `physical` and `ideal`, indicated by their `primtype` attribute. 
`PrimitiveType.IDEAL` primitives specify circuit-theoretic ideal elements 
e.g. resistors, capacitors, inductors, and notably aphysical elements 
such as ideal voltage and current sources. 

`PrimitiveType.PHYSICAL` primitives in contrast specify abstract versions 
of ultimately physically-realizable elements such as transistors and diodes. 
These elements typically require some external translation, e.g. by a process-technology 
library, to execute in simulations or to be realized in hardware. 

Many element-types (particularly passives) come in both `ideal` and `physical` flavors, 
as typical process-technologies include physical passives, but with far different 
parameterization than ideal passives. For example resistors are commonly specified 
in physical length and width. Capacitors are similarly specified in physical terms, 
often adding metal layers or other physical features. The component-value (R,C,L, etc.) 
for these physically-specified cells is commonly suggestive or optional. 

Both the `Primitive` type and all of its instances are defined in this module. 
The collection of `Primitive` instances is often referred to as Hdl21's "primitive library". 

Summary of the content of the primitive library: 

| Name                           | Description                       | Type     | Aliases                               | Ports        |
| ------------------------------ | --------------------------------- | -------- | ------------------------------------- | ------------ |
| Mos                            | Mos Transistor                    | PHYSICAL | MOS                                   | d, g, s, b   |
| IdealResistor                  | Ideal Resistor                    | IDEAL    | R, Res, Resistor, IdealR, IdealRes    | p, n         |
| PhysicalResistor               | Physical Resistor                 | PHYSICAL | PhyR, PhyRes, ResPhy, PhyResistor     | p, n         |
| ThreeTerminalResistor          | Three Terminal Resistor           | PHYSICAL | Res3, PhyRes3, ResPhy3, PhyResistor3  | p, n, b      |
| IdealCapacitor                 | Ideal Capacitor                   | IDEAL    | C, Cap, Capacitor, IdealC, IdealCap   | p, n         |
| PhysicalCapacitor              | Physical Capacitor                | PHYSICAL | PhyC, PhyCap, CapPhy, PhyCapacitor    | p, n         |
| ThreeTerminalCapacitor         | Three Terminal Capacitor          | PHYSICAL | Cap3, PhyCap3, CapPhy3, PhyCapacitor3 | p, n, b      |
| IdealInductor                  | Ideal Inductor                    | IDEAL    | L, Ind, Inductor, IdealL, IdealInd    | p, n         |
| PhysicalInductor               | Physical Inductor                 | PHYSICAL | PhyL, PhyInd, IndPhy, PhyInductor     | p, n         |
| ThreeTerminalInductor          | Three Terminal Inductor           | PHYSICAL | Ind3, PhyInd3, IndPhy3, PhyInductor3  | p, n, b      |
| PhysicalShort                  | Short-Circuit/ Net-Tie            | PHYSICAL | Short                                 | p, n         |
| DcVoltageSource                | DC Voltage Source                 | IDEAL    | V, Vdc, Vsrc                          | p, n         |
| PulseVoltageSource             | Pulse Voltage Source              | IDEAL    | Vpu, Vpulse                           | p, n         |
| CurrentSource                  | Ideal DC Current Source           | IDEAL    | I, Idc, Isrc                          | p, n         |
| VoltageControlledVoltageSource | Voltage Controlled Voltage Source | IDEAL    | Vcvs, VCVS                            | p, n, cp, cn |
| CurrentControlledVoltageSource | Current Controlled Voltage Source | IDEAL    | Ccvs, CCVS                            | p, n, cp, cn |
| VoltageControlledCurrentSource | Voltage Controlled Current Source | IDEAL    | Vccs, VCCS                            | p, n, cp, cn |
| CurrentControlledCurrentSource | Current Controlled Current Source | IDEAL    | Cccs, CCCS                            | p, n, cp, cn |
| Bipolar                        | Bipolar Transistor                | PHYSICAL | Bjt, BJT                              | c, b, e      |
| Diode                          | Diode                             | PHYSICAL | D                                     | p, n         |

"""

# Non-docstring comment:
#
# That big table above is also included in the Hdl21 package documentation.
# It is generated by the script `Hdl21/scripts/primtable.py`,
# which imports the contents of this module and prints a line per primitive.
# On changes to this module, re-run the script, paste the table here and anywhere else it is used.

# Std-Lib Imports
import copy
from enum import Enum
from dataclasses import replace
from typing import Optional, Any, List, Type, Dict

# PyPi Imports
from pydantic.dataclasses import dataclass

# Local imports
from .default import Default
from .call import param_call
from .params import paramclass, Param, isparamclass, NoParams, _unique_name
from .signal import Port, Signal, Visibility
from .instance import calls_instantiate
from .scalar import Scalar


class PrimitiveType(Enum):
    """Enumerated Primitive-Types"""

    IDEAL = "IDEAL"
    PHYSICAL = "PHYSICAL"


@dataclass
class Primitive:
    """# Hdl21 Primitive Component

    Primitives are leaf-level Modules typically defined not by users,
    but by simulation tools or device fabricators.
    Prominent examples include MOS transistors, diodes, resistors, and capacitors.
    """

    name: str  # Primitive Name
    desc: str  # String Description
    port_list: List[Signal]  # Ordered Port List
    paramtype: Type  # Class/ Type of valid Parameters
    primtype: PrimitiveType  # Ideal vs Physical Primitive-Type

    def __post_init_post_parse__(self):
        """After type-checking, do plenty more checks on values"""
        if not isparamclass(self.paramtype):
            msg = f"Invalid Primitive param-type {self.paramtype} for {self.name}, must be an `hdl21.paramclass`"
            raise TypeError(msg)
        for p in self.port_list:
            if not p.name:
                raise ValueError(f"Unnamed Primitive Port {p} for {self.name}")
            if p.vis != Visibility.PORT:
                msg = f"Invalid Primitive Port {p.name} on {self.name}; must have PORT visibility"
                raise ValueError(msg)

    def __call__(self, arg: Any = Default, **kwargs) -> "PrimitiveCall":
        params = param_call(callee=self, arg=arg, **kwargs)
        return PrimitiveCall(prim=self, params=params)

    @property
    def Params(self) -> Type:
        """Type-style alias for the parameter-type."""
        return self.paramtype

    @property
    def ports(self) -> Dict[str, Signal]:
        return {p.name: p for p in self.port_list}

    def __eq__(self, other) -> bool:
        # Identity is equality
        return other is self

    def __hash__(self) -> bool:
        # Identity is equality
        return hash(id(self))


@calls_instantiate
@dataclass
class PrimitiveCall:
    """Primitive Call
    A combination of a Primitive and its Parameter-values,
    typically generated by calling the Primitive."""

    prim: Primitive
    params: Any = NoParams

    def __post_init_post_parse__(self):
        # Type-validate our parameters
        if not isinstance(self.params, self.prim.paramtype):
            msg = f"Invalid parameters {self.params} for Primitive {self.prim}. Must be {self.prim.paramtype}"
            raise TypeError(msg)

    @property
    def name(self) -> str:
        return self.prim.name + "(" + _unique_name(self.params) + ")"

    @property
    def ports(self) -> dict:
        return self.prim.ports

    def __eq__(self, other) -> bool:
        """Call equality requires:
        * *Identity* between prims, and
        * *Equality* between parameter-values."""
        return self.prim is other.prim and self.params == other.params

    def __hash__(self):
        """Generator-Call hashing, consistent with `__eq__` above, uses:
        * *Identity* of its prim, and
        * *Value* of its parameters.
        The two are joined for hashing as a two-element tuple."""
        return hash((id(self.prim), self.params))


@dataclass
class PrimLibEntry:
    """# Entry in the Primitive Library"""

    prim: Primitive
    aliases: List[str]


# Dictionary storing all primitives, keyed by their primary name.
# Stores aliases on the side.
_primitives: Dict[str, PrimLibEntry] = dict()


def _add(prim: Primitive, aliases: List[str]) -> Primitive:
    """Add a primitive to this library.
    Ensures its identifier matches its `name` field, and adds any aliases to the global namespace.
    This is a private function and should be used solely during `hdl21.primitives` import-time."""
    global _primitives

    if prim.name in _primitives or prim.name in globals():
        raise ValueError(f"Duplicate primitive name {prim.name}")

    # Add the combination as a new entry
    entry = PrimLibEntry(prim, aliases)
    _primitives[prim.name] = entry
    globals()[prim.name] = prim

    for alias in aliases:
        if alias in _primitives or alias in globals():
            raise ValueError(f"Duplicate primitive alias {alias}")
        globals()[alias] = prim
    return prim


""" 
Mos Transistor Section 
"""


class MosType(Enum):
    """# MOS Type (NMOS/ PMOS) Enumeration"""

    NMOS = "NMOS"
    PMOS = "PMOS"


class MosVth(Enum):
    """# MOS Threshold Enumeration"""

    STD = "STD"
    LOW = "LOW"
    HIGH = "HIGH"
    ULTRA_LOW = "ULTRA_LOW"
    ZERO = "ZERO"
    NATIVE = "NATIVE"


class MosFamily(Enum):
    """# MOS Family Enumeration"""

    NONE = "NONE"
    CORE = "CORE"
    IO = "IO"
    LP = "LP"
    HP = "HP"


@paramclass
class MosParams:
    """# MOS Transistor Parameters"""

    w = Param(dtype=Optional[Scalar], desc="Width in resolution units", default=None)
    l = Param(dtype=Optional[Scalar], desc="Length in resolution units", default=None)
    npar = Param(
        dtype=Scalar, desc="Number of parallel fingers", default=1
    )  # FIXME: rename
    mult = Param(dtype=Scalar, desc="Multiplier", default=1)

    tp = Param(dtype=MosType, desc="MosType (Nmos/ Pmos)", default=MosType.NMOS)
    vth = Param(dtype=MosVth, desc="Threshold voltage specifier", default=MosVth.STD)
    family = Param(dtype=MosFamily, desc="Device family", default=MosFamily.NONE)
    model = Param(dtype=Optional[str], desc="Model (Name)", default=None)

    # def __post_init_post_parse__(self):
    #     """Value Checks"""
    #     # FIXME: re-introduce these, for the case in which the parameters are `Prefixed` and not `Literal` values.
    #     if self.w <= 0:
    #         raise ValueError(f"MosParams with invalid width {self.w}")
    #     if self.l <= 0:
    #         raise ValueError(f"MosParams with invalid length {self.l}")
    #     if self.npar <= 0:
    #         msg = f"MosParams with invalid number parallel fingers {self.npar}"
    #         raise ValueError(msg)


# Mos Transistor Ports, in SPICE Conventional Order
MosPorts = [
    Port(name="d", desc="Drain"),
    Port(name="g", desc="Gate"),
    Port(name="s", desc="Source"),
    Port(name="b", desc="Bulk"),
]

Mos = _add(
    prim=Primitive(
        name="Mos",
        desc="Mos Transistor",
        port_list=copy.deepcopy(MosPorts),
        paramtype=MosParams,
        primtype=PrimitiveType.PHYSICAL,
    ),
    aliases=["MOS"],
)


def Nmos(arg: Any = Default, **kwargs) -> Primitive:
    """Nmos Constructor. A thin wrapper around `hdl21.primitives.Mos`"""
    mos = Mos(arg, **kwargs)
    mos.params = replace(mos.params, tp=MosType.NMOS)
    return mos


def Pmos(arg: Any = Default, **kwargs) -> Primitive:
    """Pmos Constructor. A thin wrapper around `hdl21.primitives.Mos`"""
    mos = Mos(arg, **kwargs)
    mos.params = replace(mos.params, tp=MosType.PMOS)
    return mos


""" 
Passives
"""

# Oft-reused port list for the passive elements
PassivePorts = [Port(name="p"), Port(name="n")]
# And the three-terminal version
ThreeTerminalPorts = [Port(name="p"), Port(name="n"), Port(name="b")]


@paramclass
class ResistorParams:
    r = Param(dtype=Scalar, desc="Resistance (ohms)")


IdealResistor = _add(
    prim=Primitive(
        name="IdealResistor",
        desc="Ideal Resistor",
        port_list=copy.deepcopy(PassivePorts),
        paramtype=ResistorParams,
        primtype=PrimitiveType.IDEAL,
    ),
    aliases=["R", "Res", "Resistor", "IdealR", "IdealRes"],
)


@paramclass
class PhysicalResistorParams:
    w = Param(dtype=Optional[Scalar], desc="Width in resolution units", default=None)
    l = Param(dtype=Optional[Scalar], desc="Length in resolution units", default=None)
    model = Param(dtype=Optional[str], desc="Model (Name)", default=None)


PhysicalResistor = _add(
    prim=Primitive(
        name="PhysicalResistor",
        desc="Physical Resistor",
        port_list=copy.deepcopy(PassivePorts),
        paramtype=PhysicalResistorParams,
        primtype=PrimitiveType.PHYSICAL,
    ),
    aliases=["PhyR", "PhyRes", "ResPhy", "PhyResistor"],
)


ThreeTerminalResistor = _add(
    prim=Primitive(
        name="ThreeTerminalResistor",
        desc="Three Terminal Resistor",
        port_list=copy.deepcopy(ThreeTerminalPorts),
        paramtype=PhysicalResistorParams,
        primtype=PrimitiveType.PHYSICAL,
    ),
    aliases=["Res3", "PhyRes3", "ResPhy3", "PhyResistor3"],
)


@paramclass
class IdealCapacitorParams:
    c = Param(dtype=Scalar, desc="Capacitance (F)")


IdealCapacitor = _add(
    prim=Primitive(
        name="IdealCapacitor",
        desc="Ideal Capacitor",
        port_list=copy.deepcopy(PassivePorts),
        paramtype=IdealCapacitorParams,
        primtype=PrimitiveType.IDEAL,
    ),
    aliases=["C", "Cap", "Capacitor", "IdealC", "IdealCap"],
)


@paramclass
class PhysicalCapacitorParams:
    c = Param(dtype=Scalar, desc="Capacitance (F)", default=None)
    w = Param(dtype=Scalar, desc="Width in resolution units", default=None)
    l = Param(dtype=Scalar, desc="Length in resolution units", default=None)
    model = Param(dtype=Optional[str], desc="Model (Name)", default=None)
    mult = Param(dtype=Optional[str], desc="Multiplier", default=None)


PhysicalCapacitor = _add(
    prim=Primitive(
        name="PhysicalCapacitor",
        desc="Physical Capacitor",
        port_list=copy.deepcopy(PassivePorts),
        paramtype=PhysicalCapacitorParams,
        primtype=PrimitiveType.PHYSICAL,
    ),
    aliases=["PhyC", "PhyCap", "CapPhy", "PhyCapacitor"],
)


ThreeTerminalCapacitor = _add(
    prim=Primitive(
        name="ThreeTerminalCapacitor",
        desc="Three Terminal Capacitor",
        port_list=copy.deepcopy(ThreeTerminalPorts),
        paramtype=PhysicalCapacitorParams,
        primtype=PrimitiveType.PHYSICAL,
    ),
    aliases=["Cap3", "PhyCap3", "CapPhy3", "PhyCapacitor3"],
)


@paramclass
class IdealInductorParams:
    l = Param(dtype=Scalar, desc="Inductance (H)")


IdealInductor = _add(
    prim=Primitive(
        name="IdealInductor",
        desc="Ideal Inductor",
        port_list=copy.deepcopy(PassivePorts),
        paramtype=IdealInductorParams,
        primtype=PrimitiveType.IDEAL,
    ),
    aliases=["L", "Ind", "Inductor", "IdealL", "IdealInd"],
)


@paramclass
class PhysicalInductorParams:
    l = Param(dtype=Scalar, desc="Inductance (H)")


PhysicalInductor = _add(
    Primitive(
        name="PhysicalInductor",
        desc="Physical Inductor",
        port_list=copy.deepcopy(PassivePorts),
        paramtype=PhysicalInductorParams,
        primtype=PrimitiveType.PHYSICAL,
    ),
    aliases=["PhyL", "PhyInd", "IndPhy", "PhyInductor"],
)


ThreeTerminalInductor = _add(
    prim=Primitive(
        name="ThreeTerminalInductor",
        desc="Three Terminal Inductor",
        port_list=copy.deepcopy(ThreeTerminalPorts),
        paramtype=PhysicalInductorParams,
        primtype=PrimitiveType.PHYSICAL,
    ),
    aliases=["Ind3", "PhyInd3", "IndPhy3", "PhyInductor3"],
)


@paramclass
class PhysicalShortParams:
    layer = Param(dtype=Optional[Scalar], desc="Metal layer", default=None)
    w = Param(dtype=Optional[Scalar], desc="Width in resolution units", default=None)
    l = Param(dtype=Optional[Scalar], desc="Length in resolution units", default=None)


PhysicalShort = _add(
    prim=Primitive(
        name="PhysicalShort",
        desc="Short-Circuit/ Net-Tie",
        port_list=copy.deepcopy(PassivePorts),
        paramtype=PhysicalShortParams,
        primtype=PrimitiveType.PHYSICAL,
    ),
    aliases=["Short"],
)


""" 
Sources
"""


@paramclass
class DcVoltageSourceParams:
    """`DcVoltageSource` Parameters"""

    dc = Param(dtype=Optional[Scalar], default=0, desc="DC Value (V)")
    ac = Param(dtype=Optional[Scalar], default=None, desc="AC Amplitude (V)")


DcVoltageSource = _add(
    prim=Primitive(
        name="DcVoltageSource",
        desc="DC Voltage Source",
        port_list=copy.deepcopy(PassivePorts),
        paramtype=DcVoltageSourceParams,
        primtype=PrimitiveType.IDEAL,
    ),
    aliases=[
        "V",
        "Vdc",
        "Vsrc",
    ],
)


@paramclass
class PulseVoltageSourceParams:
    """`PulseVoltageSource` Parameters"""

    delay = Param(dtype=Optional[Scalar], default=None, desc="Time Delay (s)")
    v1 = Param(dtype=Optional[Scalar], default=None, desc="One Value (V)")
    v2 = Param(dtype=Optional[Scalar], default=None, desc="Zero Value (V)")
    period = Param(dtype=Optional[Scalar], default=None, desc="Period (s)")
    rise = Param(dtype=Optional[Scalar], default=None, desc="Rise time (s)")
    fall = Param(dtype=Optional[Scalar], default=None, desc="Fall time (s)")
    width = Param(dtype=Optional[Scalar], default=None, desc="Pulse width (s)")


PulseVoltageSource = _add(
    prim=Primitive(
        name="PulseVoltageSource",
        desc="Pulse Voltage Source",
        port_list=copy.deepcopy(PassivePorts),
        paramtype=PulseVoltageSourceParams,
        primtype=PrimitiveType.IDEAL,
    ),
    aliases=["Vpu", "Vpulse"],
)

Vpu = PulseVoltageSource
Vpulse = PulseVoltageSource


@paramclass
class SineVoltageSourceParams:
    """`SineVoltageSource` Parameters"""

    voff = Param(dtype=Optional[Scalar], default=None, desc="Offset (V)")
    vamp = Param(dtype=Optional[Scalar], default=None, desc="Amplitude (V)")
    freq = Param(dtype=Optional[Scalar], default=None, desc="Frequency (Hz)")
    td = Param(dtype=Optional[Scalar], default=None, desc="Delay (s)")
    phase = Param(dtype=Optional[Scalar], default=None, desc="Phase at td (degrees)")


SineVoltageSource = _add(
    prim=Primitive(
        name="SineVoltageSource",
        desc="Sine Voltage Source",
        port_list=copy.deepcopy(PassivePorts),
        paramtype=SineVoltageSourceParams,
        primtype=PrimitiveType.IDEAL,
    ),
    aliases=["Vsin"],
)


@paramclass
class CurrentSourceParams:
    dc = Param(dtype=Optional[Scalar], default=0, desc="DC Value (A)")


CurrentSource = _add(
    Primitive(
        name="CurrentSource",
        desc="Ideal DC Current Source",
        port_list=copy.deepcopy(PassivePorts),
        paramtype=CurrentSourceParams,
        primtype=PrimitiveType.IDEAL,
    ),
    aliases=["I", "Idc", "Isrc"],
)


"""
Controlled Sources 
"""


@paramclass
class ControlledSourceParams:
    gain = Param(dtype=Scalar, default=1, desc="Gain in SI Units")


# Controlled Sources Port List
ControlledSourcePorts = [
    Port(name="p", desc="Output, Positive"),
    Port(name="n", desc="Output, Negative"),
    Port(name="cp", desc="Control, Positive"),
    Port(name="cn", desc="Control, Negative"),
]

VoltageControlledVoltageSource = _add(
    prim=Primitive(
        name="VoltageControlledVoltageSource",
        desc="Voltage Controlled Voltage Source",
        port_list=copy.deepcopy(ControlledSourcePorts),
        paramtype=ControlledSourceParams,
        primtype=PrimitiveType.IDEAL,
    ),
    aliases=["Vcvs", "VCVS"],
)
CurrentControlledVoltageSource = _add(
    prim=Primitive(
        name="CurrentControlledVoltageSource",
        desc="Current Controlled Voltage Source",
        port_list=copy.deepcopy(ControlledSourcePorts),
        paramtype=ControlledSourceParams,
        primtype=PrimitiveType.IDEAL,
    ),
    aliases=["Ccvs", "CCVS"],
)
VoltageControlledCurrentSource = _add(
    prim=Primitive(
        name="VoltageControlledCurrentSource",
        desc="Voltage Controlled Current Source",
        port_list=copy.deepcopy(ControlledSourcePorts),
        paramtype=ControlledSourceParams,
        primtype=PrimitiveType.IDEAL,
    ),
    aliases=["Vccs", "VCCS"],
)
CurrentControlledCurrentSource = _add(
    prim=Primitive(
        name="CurrentControlledCurrentSource",
        desc="Current Controlled Current Source",
        port_list=copy.deepcopy(ControlledSourcePorts),
        paramtype=ControlledSourceParams,
        primtype=PrimitiveType.IDEAL,
    ),
    aliases=["Cccs", "CCCS"],
)

""" 
Bipolar Section 
"""


class BipolarType(Enum):
    """Bipolar Junction Transistor NPN/PNP Type Enumeration"""

    NPN = "NPN"
    PNP = "PNP"


@paramclass
class BipolarParams:
    """Bipolar Transistor Parameters"""

    w = Param(dtype=Optional[Scalar], desc="Width in resolution units", default=None)
    l = Param(dtype=Optional[Scalar], desc="Length in resolution units", default=None)
    tp = Param(
        dtype=BipolarType, desc="Bipolar Type (NPN/ PNP)", default=BipolarType.NPN
    )
    model = Param(dtype=Optional[str], desc="Model (Name)", default=None)
    mult = Param(dtype=Optional[Scalar], desc="Multiplier", default=None)

    def __post_init_post_parse__(self):
        """Value Checks"""
        if self.w <= 0:
            raise ValueError(f"BipolarParams with invalid width {self.w}")
        if self.l <= 0:
            raise ValueError(f"BipolarParams with invalid length {self.l}")


BipolarPorts = [Port(name="c"), Port(name="b"), Port(name="e")]

Bipolar = _add(
    prim=Primitive(
        name="Bipolar",
        desc="Bipolar Transistor",
        port_list=copy.deepcopy(BipolarPorts),
        paramtype=BipolarParams,
        primtype=PrimitiveType.PHYSICAL,
    ),
    aliases=["Bjt", "BJT"],
)


def Npn(arg: Any = Default, **kwargs) -> Primitive:
    """Npn Constructor. A thin wrapper around `hdl21.primitives.Bipolar`"""
    bip = Bipolar(arg, **kwargs)
    bip.params = replace(bip.params, tp=BipolarType.NPN)
    return bip


def Pnp(arg: Any = Default, **kwargs) -> Primitive:
    """Pnp Constructor. A thin wrapper around `hdl21.primitives.Bipolar`"""
    bip = Bipolar(arg, **kwargs)
    bip.params = replace(bip.params, tp=BipolarType.PNP)
    return bip


""" 
Diodes
"""


@paramclass
class DiodeParams:
    w = Param(dtype=Optional[Scalar], desc="Width in resolution units", default=None)
    l = Param(dtype=Optional[Scalar], desc="Length in resolution units", default=None)
    model = Param(dtype=Optional[str], desc="Model (Name)", default=None)


Diode = _add(
    prim=Primitive(
        name="Diode",
        desc="Diode",
        # Despite not really being "passive", Diode does use the same `PassivePorts` list.
        port_list=copy.deepcopy(PassivePorts),
        paramtype=DiodeParams,
        primtype=PrimitiveType.PHYSICAL,
    ),
    aliases=["D"],
)
