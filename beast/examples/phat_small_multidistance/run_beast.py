#!/usr/bin/env python
"""
Script to run the BEAST on the PHAT-like data.
Assumes that the datamodel.py file exists in the same directory as this script.
  And it must be called datamodel.py 
     used in make_model.py code in physicsmodel, more recoding needed to remove
     this dependency
"""

# system imports
from __future__ import (absolute_import, division, print_function)
import sys
import argparse
import time
import string
import numpy as np

from astropy import units

# BEAST imports
from beast.physicsmodel.create_project_dir import create_project_dir
from beast.physicsmodel.model_grid import (make_iso_table,
                                           make_spectral_grid,
                                           add_stellar_priors,
                                           make_grid_with_distances,
                                           make_extinguished_sed_grid)

import beast.observationmodel.noisemodel.generic_noisemodel as noisemodel
from beast.observationmodel.ast.make_ast_input_list import pick_models
from beast.observationmodel.ast.make_ast_xy_list import pick_positions
from beast.fitting import fit
from beast.fitting import trim_grid
from beast.physicsmodel.grid import FileSEDGrid
from beast.tools import verify_params


import datamodel


if __name__ == '__main__':
    # commandline parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--physicsmodel",
                        help="Generate the physics model grid",
                        action="store_true")
    parser.add_argument("-a", "--ast", help="Generate an input AST file",
                        action="store_true")
    parser.add_argument("-o", "--observationmodel",
                        help="Calculate the observation model (bias and noise)",
                        action="store_true")
    parser.add_argument("-t", "--trim",
                        help="Trim the physics and observation model grids",
                        action="store_true")
    parser.add_argument("-f", "--fit", help="Fit the observed data",
                        action="store_true")
    parser.add_argument("-r", "--resume", help="Resume a fitting run",
                        action="store_true")
    args = parser.parse_args()

    # check input parameters, print what is the problem, stop run_beast
    verify_params.verify_input_format(datamodel)

    if args.physicsmodel:

        # make sure the project directory exists
        pdir = create_project_dir(datamodel.project)

        # download and load the isochrones
        (iso_fname, oiso) = make_iso_table(datamodel.project,
                                           oiso=datamodel.oiso,
                                           logtmin=datamodel.logt[0],
                                           logtmax=datamodel.logt[1],
                                           dlogt=datamodel.logt[2],
                                           z=datamodel.z)

        # calculate the distances in pc
        distance_unit = datamodel.distances[0].unit
        if distance_unit == units.mag:
            dmods = np.array([d.value for d in datamodel.distances])
            distances = np.power(10, dmods / 5. + 1) * units.pc
        elif distance_unit == units.pc:
            distances = datamodel.distances
        else:
            raise ValueError("distance modulus does not have mag or parsec units")

        if hasattr(datamodel, 'add_spectral_properties_kwargs'):
            extra_kwargs = datamodel.add_spectral_properties_kwargs
        else:
            extra_kwargs = None

        # generate the spectral library (no dust extinction)
        (spec_fname, g_spec) = make_spectral_grid(
            datamodel.project,
            oiso,
            osl=datamodel.osl,
            distances=distances,
            add_spectral_properties_kwargs=extra_kwargs)

        # add the stellar priors as weights
        #   also computes the grid weights for the stellar part
        (pspec_fname, g_pspec) = add_stellar_priors(datamodel.project,
                                                    g_spec)

        g_pdist_pspec = make_grid_with_distances(datamodel.project, g_pspec, distances)
        # override for debug
        # g_pdist_pspec = g_pspec

        # generate the SED grid by integrating the filter response functions
        #   effect of dust extinction applied before filter integration
        #   also computes the dust priors as weights
        (seds_fname, g_seds) = make_extinguished_sed_grid(
            datamodel.project,
            g_pdist_pspec,
            datamodel.filters,
            extLaw=datamodel.extLaw,
            av=datamodel.avs,
            rv=datamodel.rvs,
            fA=datamodel.fAs,
            rv_prior_model=datamodel.rv_prior_model,
            av_prior_model=datamodel.av_prior_model,
            fA_prior_model=datamodel.fA_prior_model,
            add_spectral_properties_kwargs=extra_kwargs)

    if args.ast:
        # get the modesedgrid on which to grab input AST
        modelsedgridfile = datamodel.project + '/' + datamodel.project + \
            '_seds.grid.hd5'
        modelsedgrid = FileSEDGrid(modelsedgridfile)

        N_models = datamodel.ast_models_selected_per_age
        Nfilters = datamodel.ast_bands_above_maglimit
        Nrealize = datamodel.ast_realization_per_model
        mag_cuts = datamodel.ast_maglimit

        if len(mag_cuts) == 1:
            tmp_cuts = mag_cuts
            obsdata = datamodel.get_obscat(datamodel.obsfile,
                                           datamodel.filters)

            min_mags = np.zeros(len(datamodel.filters))
            for k, filtername in enumerate(obsdata.filters):
                sfiltername = obsdata.data.resolve_alias(filtername)
                sfiltername = sfiltername.replace('rate', 'vega')
                sfiltername = sfiltername.replace('RATE', 'VEGA')
                keep, = np.where(obsdata[sfiltername] < 99.)
                min_mags[k] = np.percentile(obsdata[keep][sfiltername], 90.)

            # max. mags from the gst observation cat.
            mag_cuts = min_mags + tmp_cuts

        pick_models(modelsedgrid, mag_cuts, Nfilter=Nfilters,
                    N_stars=N_models, Nrealize=Nrealize)

        if datamodel.ast_with_positions == True:
            separation = datamodel.ast_pixel_distribution
            filename = datamodel.project + '/' + datamodel.project + '_inputAST.txt'

            if datamodel.ast_reference_image is not None:
                pick_positions(filename, separation,
                               refimage=datamodel.ast_reference_image)
            else:
                pick_positions(filename, separation)

    if args.observationmodel:
        print('Generating noise model from ASTs and absflux A matrix')

        # get the modesedgrid on which to generate the noisemodel
        modelsedgridfile = datamodel.project + '/' + datamodel.project + \
            '_seds.grid.hd5'
        modelsedgrid = FileSEDGrid(modelsedgridfile)

        # generate the AST noise model
        noisemodel.make_toothpick_noise_model(
            datamodel.noisefile,
            datamodel.astfile,
            modelsedgrid,
            absflux_a_matrix=datamodel.absflux_a_matrix)

    if args.trim:
        print('Trimming the model and noise grids')

        # read in the observed data
        obsdata = datamodel.get_obscat(datamodel.obsfile,
                                       datamodel.filters)

        # get the modesedgrid on which to generate the noisemodel
        modelsedgridfile = datamodel.project + '/' + datamodel.project + \
            '_seds.grid.hd5'
        modelsedgrid = FileSEDGrid(modelsedgridfile)

        # read in the noise model just created
        noisemodel_vals = noisemodel.get_noisemodelcat(datamodel.noisefile)

        # trim the model sedgrid
        sed_trimname = modelsedgridfile.replace('_seds', '_seds_trim')
        noisemodel_trimname = sed_trimname.replace('_seds', '_noisemodel')

        trim_grid.trim_models(modelsedgrid, noisemodel_vals, obsdata,
                              sed_trimname, noisemodel_trimname, sigma_fac=3.)

    if args.fit:
        start_time = time.clock()

        # the files for the trimmed model grid and noisemodel grid
        modelsedgrid = datamodel.project + '/' + datamodel.project + \
            '_seds_trim.grid.hd5'
        noisemodelfile = modelsedgrid.replace('_seds', '_noisemodel')

        # read in the the AST noise model
        noisemodel_vals = noisemodel.get_noisemodelcat(noisemodelfile)

        # read in the observed data
        obsdata = datamodel.get_obscat(datamodel.obsfile,
                                       datamodel.filters)

        # output files
        print(datamodel.project)
        statsfile = datamodel.project + '/' + datamodel.project + \
            '_stats.fits'
        pdf1dfile = statsfile.replace('stats.fits', 'pdf1d.fits')
        lnpfile = statsfile.replace('stats.fits', 'lnp.hd5')

        fit.summary_table_memory(obsdata, noisemodel_vals, modelsedgrid,
                                 resume=args.resume,
                                 threshold=-10., save_every_npts=100,
                                 lnp_npts=60,
                                 stats_outname=statsfile,
                                 pdf1d_outname=pdf1dfile,
                                 lnp_outname=lnpfile)

        new_time = time.clock()
        print('time to fit: ', (new_time - start_time) / 60., ' min')

    # print help if no arguments
    if not any(vars(args).values()):
        parser.print_help()
