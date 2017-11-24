from fenics import *
import scipy.interpolate as interp
import numpy as np
import matplotlib.pyplot as plt
import test_domains
import fenics_util as fu


#Number of cells in grid
nx = 481;
ny = 481;

#Fenics mesh
L = 240e3
mesh = RectangleMesh(Point(0,0), Point(L, L), nx, ny)
V = FunctionSpace(mesh, 'Lagrange',1)
v = Function(V)
n = V.dim()
d = mesh.geometry().dim()

dof_coordinates = V.tabulate_dof_coordinates()
dof_coordinates.resize((n, d))
dof_x = dof_coordinates[:, 0]
dof_y = dof_coordinates[:, 1]

#Sampling Mesh, identical to Fenics mesh
domain = test_domains.analytical1(L,nx=nx+1,ny=ny+1)
xcoord = domain.x
ycoord = domain.y

#Data is not stored in an ordered manner on the fencis mesh.
#Using interpolation function to get correct grid ordering
bed_interp = interp.RectBivariateSpline(xcoord,ycoord, domain.bed)
surf_interp = interp.RectBivariateSpline(xcoord,ycoord, domain.surf)
bmelt_interp = interp.RectBivariateSpline(xcoord,ycoord, domain.bmelt)
B2_interp = interp.RectBivariateSpline(xcoord,ycoord, domain.B2)

#Coordinates of DOFS of fenics mesh in order data is stored
bed = bed_interp.ev(dof_x, dof_y)
surf = surf_interp.ev(dof_x, dof_y)
bmelt = bmelt_interp.ev(dof_x, dof_y)
B2 = B2_interp.ev(dof_x, dof_y)

#Save mesh and data points at coordinates
dd = '../input/analytical1/'

File(''.join([dd,'analytical1_mesh.xml'])) << mesh

v.vector()[:] = bed.flatten()
File(''.join([dd,'analytical1_mesh_bed.xml'])) <<  v

v.vector()[:] = surf.flatten()
File(''.join([dd,'analytical1_mesh_surf.xml'])) <<  v

v.vector()[:] = bmelt.flatten()
File(''.join([dd,'analytical1_mesh_bmelt.xml'])) <<  v

v.vector()[:] = B2.flatten()
File(''.join([dd,'analytical1_mesh_B2.xml'])) <<  v