import math
import random
from circle import Circle

in_port  = 10000
out_port = 10001
plaxis_path = r'C:\Program Files (x86)\Plaxis\PLAXIS 2D' #no trailing backslash!

# Create a random displacement for the given lines and phase, with a maximum length u
def random_displacement(phases, lines, u):
    from math import sin, cos, pi # You could also do "import math" and refer to e.g. "math.sin()"

    for phase in phases:
        alpha = random.uniform(0, 2*pi)
        x = u * sin(alpha)
        y = u * cos(alpha)

        dx = 'Prescribed'
        dy = 'Prescribed'

        # Is this what we want?
        if not x:
            dx = 'Free'

        if not y:
            dy = 'Free'

        for line in lines:
            line.Displacement_x[phase] = dx
            line.Displacement_y[phase] = dy
            line.ux_start[phase] = x
            line.uy_start[phase] = y
            line.u_start[phase] = u

import imp
found_module = imp.find_module('plxscripting', [plaxis_path])
plxscripting = imp.load_module('plxscripting', *found_module)
from plxscripting.easy import *

s_i, g_i = new_server('localhost', in_port)
s_o, g_o = new_server('localhost', out_port)

s_i.new()

# Set the general variables
pile_radius = 2.5
mesh_refinement_radius = pile_radius + 4
circle_inc = 5
xmax = 20
xmin = -20
ymax = 20
ymin = -20
bc_load = 100       # load for creating boundary condition that creates isitropic stress state
u = 0.1

# Create the materials
material_sand = g_i.soilmat()
#print(str(dir(material_sand)))
material_sand.setproperties(
    "MaterialName", "Sanisand",
    "Colour",       1706150,
    "SoilModel",    100,
    "UserDLLName",  "twosurface_m.dll",
    "UserModel",    "TwoSurfaceModel",
    "User1",        100.0,      #p_atm
    "User2",        0.9340,     #e_cref
    "User3",        0.01900,    # lambda
    "User4",        0.7000,     # eta
    "User5",        1.250,      # M_c
    "User6",        0.8900,     # M_e
    "User7",        0.01000,    # m_0
    "User8",        125.0,      # G_0
    "User9",        0.05000,    # v
    "User10",       7.050,      # h_0
    "User11",       0.9680,     # c_h
    "User12",       1.100,      # n_c^b
    "User13",       0.7040,     # A_0
    "User14",       3.500,      # n_c^d
    "User15",       4.000,      # Z_max
    "User16",       600.0,      # c_z
    "User17",       10e3,       # ???
    "User18",       0.8080,     # e_0
    "User19",       1.100,      # n_e^b
    "User20",       3.500,      # n_e^d
    "User21",       0.9340,     # e_c_ref^e
    "Gref",         90.909,     # in PLAXIS only E can be entered (E=1000 from Ana-> high number to imitate rigid body?), here divide E by 11 (no idea why!)
    "cref",         10)         # copied from Ana Risueno

material_pile = g_i.soilmat()
material_pile.setproperties(
    "MaterialName", "Pile",
    "Colour",       1207539,
    "SoilModel",    1,          # Linear Elastic
    "Gref",         334.4e6,
    "Eoed",         33.78e9,
    "nu",           0.4950)

material_interface = g_i.soilmat()
material_interface.setproperties(
    "MaterialName", "Interface",
    "Colour",       6286105,
    "SoilModel",    2,          # Mohr-Coulomb Model
    "gammaUnsat",   0,
    "gammaSat",     0,
    "Gref",         3344,
    "nu",           0.4950,
    "cref",         1000,
    "phi",          20)

# Initialize the model boundaries (xmin, ymin, xmax, ymax)
g_i.Soilcontour.initializerectangular(xmin, ymin, xmax, ymax)

# Initialize the borehold that makes up the cross-section
g_i.borehole(0)
#g_i.borehole(0)

# Initialize the soil layering
g_i.sl(20)  # sand, thickness 40 m

# Set layer heights along borehole
g_i.setsoillayerlevel(g_i.Borehole_1, 0, ymax)

# Set head level
g_i.set(g_i.Borehole_1.Head, -20)

# Assign the materials
g_i.setmaterial(g_i.Soil_1, material_sand)
#g_i.setmaterial(g_i.Soil_2, material_sand)


# Create the outer box for defining the boundaries
a, b, left   = g_i.line((xmin, ymin), (xmin, ymax))
a, b, right  = g_i.line((xmax, ymin), (xmax, ymax))
a, b, top    = g_i.line((xmin, ymax), (xmax, ymax))
a, b, bottom = g_i.line((xmin, ymin), (xmax, ymin))

# Create line loads (boundary conditions)
load = g_i.lineload(left)
load.qx_start = bc_load
load.qy_start = 0

load = g_i.lineload(right)
load.qx_start = -bc_load
load.qy_start = 0

load = g_i.lineload(bottom)
load.qx_start = 0
load.qy_start = bc_load

load = g_i.lineload(top)
load.qx_start = 0
load.qy_start = -bc_load

# Create group for boundary loads
bc_load_group = g_i.group(left, right, bottom, top)
g_i.rename(bc_load_group, "bc_load_group")

# Add mesh refinement polygon
circle = Circle(r=mesh_refinement_radius, n=circle_inc)
refinement_poly, refinement_soil = g_i.polygon(*(circle.points))

# Add pile polygon and apply material
circle = Circle(r=pile_radius, n=circle_inc)
disc_poly, disc_soil = g_i.polygon(*(circle.points))
#disc_poly.material = material_pile
g_i.setmaterial(g_i.Soil_3, material_pile)

# Create line group for applying interface elements
disc_poly_group = g_i.group(disc_poly)
g_i.rename(disc_poly_group, "disc_group")

# Add lines congruent to soil polygon to apply interfaces (because Plaxis is retarded)
disc_lines = []
for segment in circle.segments():
    point_a, point_b, line = g_i.line(*segment)
    disc_lines.append(line)

# Create line displacement group
disc_line_group = g_i.group(*disc_lines)
g_i.rename(disc_line_group, "line_displ_group")

# Add interface to the group and add material
disc_interface_properties = [
    disc_line_group,
    ('MaterialMode', 'Custom'),
    ('Material', material_interface)
]
disc_interface = g_i.neginterface(*disc_interface_properties)
#disc_interface = g_i.neginterface(disc_line_group, ('MaterialMode', 'Custom'), ('Material', material_interface))

interface_group = g_i.group(disc_interface)
g_i.rename(interface_group, "interface_group")

# DISPLACEMENTS
# Initial displacement
initial_displacement_properties = [
    disc_line_group,
    ('Displacement_x', 'Prescribed'),
    ('Displacement_y', 'Free'),
    ('ux_start', 0.1)
]
displ = g_i.linedispl(*initial_displacement_properties)

# Secondary displacement
# displ = g_i.linedispl(disc_line_group, ('uy_start', 0.05))

# MESH
g_i.gotomesh()

for i in range(4):
    g_i.coarsen(top)

# g_i.refine(refinement_poly) # turn on later!!

g_i.mesh(0.06)

# Flow conditions - default

# Staged construction
g_i.gotostages()

phases = []
phase0 = g_i.InitialPhase
phase1 = g_i.phase(g_i.Phases[0])      # Equilibrium phase
phase2 = g_i.phase(g_i.Phases[1])       # Turn on initial displacement x = 0.1 m, No. in parantheses defines the starting point of the phase
phase3 = g_i.phase(g_i.Phases[1])
all_phases = (phase1, phase2, phase3)
displacement_phases = all_phases[1:]

g_i.activate(interface_group, all_phases)
g_i.activate(bc_load_group,(phase0, *all_phases))
g_i.activate(disc_line_group, phase2)

# Fetch the staged LineDisplacements, then set a random value for ux_start in phase2+
line_displ = g_i.LineDisplacements
#for phase in displacement_phases:
#    line_displ[0].ux_start[phase] = random()

# Go through all the line displacements and set the ux_start value
#for d in line_displ:
#    d.Displacement_x[phase2] = 'Prescribed'
#    d.Displacement_y[phase2] = 'Free'
#    d.ux_start[phase2] = 0.2

#for d in line_displ:
#    d.Displacement_x[phase3] = 'Prescribed'
#    d.Displacement_y[phase3] = 'Free'
#    d.ux_start[phase3] = 0.4

random_displacement(displacement_phases, line_displ, u)

# CALCULATION
g_i.calculate()
