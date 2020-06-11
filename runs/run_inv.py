import sys
import os
import argparse
from pathlib import Path
from dolfin import *
from tlm_adjoint_fenics import *

from fenics_ice import model, solver, inout
from fenics_ice import mesh as fice_mesh
from fenics_ice.config import ConfigParser
import fenics_ice.fenics_util as fu

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import time
import datetime
import pickle
from IPython import embed

def run_inv(config_file):
    """
    Run the inversion part of the simulation
    """

    # Read run config file
    params = ConfigParser(config_file)

    log = inout.setup_logging(params)
    inout.log_git_info()

    log.info("\n\n==================================")
    log.info("==  RUNNING INVERSE MODEL PHASE ==")
    log.info("==================================\n\n")

    inout.print_config(params)
    dd = params.io.input_dir

    # Load the static model data (geometry, smb, etc)
    data_file = params.io.data_file
    input_data = inout.InputData(Path(dd) / data_file)

    # Get the model mesh
    mesh = fice_mesh.get_mesh(params)
    mdl = model.model(mesh, input_data, params)

    pts_lengthscale = params.obs.pts_len

    mdl.bed_from_data()
    mdl.thick_from_data()
    mdl.gen_surf()
    mdl.mask_from_data()
    mdl.init_vel_obs()
    mdl.bmelt_from_data()
    mdl.smb_from_data()
    mdl.init_lat_dirichletbc()
    mdl.label_domain()

    mdl.gen_alpha()

    # Add random noise to Beta field iff we're inverting for it
    mdl.bglen_from_data()
    mdl.init_beta(mdl.bglen_to_beta(mdl.bglen), params.inversion.beta_active)

    # Next line will output the initial guess for alpha fed into the inversion
    # File(os.path.join(outdir,'alpha_initguess.pvd')) << mdl.alpha

    #####################
    # Run the Inversion #
    #####################

    slvr = solver.ssa_solver(mdl)
    slvr.inversion()

    ###########################
    #  Write out variables    #
    ###########################

    outdir = params.io.output_dir

    # Required for next phase (HDF5):

    invout_file = params.io.inversion_file
    invout = HDF5File(mesh.mpi_comm(), str(Path(outdir)/invout_file), 'w')

    invout.parameters.add("gamma_alpha", slvr.gamma_alpha)
    invout.parameters.add("delta_alpha", slvr.delta_alpha)
    invout.parameters.add("gamma_beta", slvr.gamma_beta)
    invout.parameters.add("delta_beta", slvr.delta_beta)
    invout.parameters.add("timestamp", str(datetime.datetime.now()))

    invout.write(mdl.alpha, 'alpha')
    invout.write(mdl.beta, 'beta')

    # For visualisation (XML & VTK):

    inout.write_variable(slvr.U, params)
    inout.write_variable(slvr.beta, params)
    inout.write_variable(slvr.beta_bgd, params, name="beta_bgd")
    inout.write_variable(mdl.bed, params, name="bed")
    H = project(mdl.H, mdl.M)
    inout.write_variable(H, params, name="thick")
    inout.write_variable(mdl.mask, params, name="mask")
    inout.write_variable(mdl.mask_vel_M, params, name="mask_vel")

    inout.write_variable(mdl.u_obs_Q, params, name="u_obs")
    inout.write_variable(mdl.v_obs_Q, params, name="v_obs")
    inout.write_variable(mdl.u_std_Q, params, name="u_std")
    inout.write_variable(mdl.v_std_Q, params, name="v_std")

    U_obs = project((mdl.v_obs_Q**2 + mdl.u_obs_Q**2)**(1.0/2.0), mdl.M)
    inout.write_variable(U_obs, params, name="uv_obs")

    inout.write_variable(slvr.alpha, params, name="alpha")

    Bglen = project(slvr.beta_to_bglen(slvr.beta), mdl.M)
    inout.write_variable(Bglen, params, name="Bglen")
    inout.write_variable(slvr.bmelt, params, name="bmelt")
    inout.write_variable(slvr.smb, params, name="smb")
    inout.write_variable(mdl.surf, params, name="surf")

if __name__ == "__main__":
    stop_annotating()
    assert len(sys.argv) == 2, "Expected a configuration file (*.toml)"
    run_inv(sys.argv[1])
