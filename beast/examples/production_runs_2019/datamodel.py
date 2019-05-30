""" Data Model interface v2.0
BEAST datamodel for LMC METAL fields
"""
from __future__ import (absolute_import, division, print_function)

import numpy as np

from astropy import units

# BEAST imports
from beast.physicsmodel.stars import isochrone
from beast.physicsmodel.stars import stellib
from beast.physicsmodel.dust import extinction
from beast.observationmodel.observations import Observations
from beast.observationmodel.vega import Vega
from beast.observationmodel.noisemodel import absflux_covmat

#from extra_filters import make_integration_filter, make_top_hat_filter

#-----------------------------------------------------------------
# User inputs                                   [sec:conf]
#-----------------------------------------------------------------
# Parameters that are required to make models
# and to fit the data
#-----------------------------------------------------------------
# AC == authomatically created
# indicates where user's input change is NOT necessary/recommended
#-----------------------------------------------------------------

# project : string
#   the name of the output results directory
project = 'LMC-5665ne-12232_beast_small'

# name of the survey
#  used for the creation of the unique name for each source
surveyname = 'METAL'

# filters : list of strings
#   full filter names in BEAST filter database
filters = ['HST_WFC3_F225W','HST_WFC3_F275W','HST_WFC3_F336W','HST_ACS_WFC_F475W','HST_ACS_WFC_F814W','HST_WFC3_F110W','HST_WFC3_F160W'] 


# basefilters : list of strings
#   short names for filters
basefilters = ['F225W','F275W','F336W','F475W','F814W','F110W','F160W'] 

# obs_colnames : list of strings
#   names of columns for filters in the observed catalog
#   need to match column names in the observed catalog,
#   input data MUST be in fluxes, NOT in magnitudes 
#   fluxes MUST be in normalized Vega units
obs_colnames = [ f.upper() + '_RATE' for f in basefilters ]

# obsfile : string 
#   pathname of the observed catalog
obsfile = 'data/14675_LMC-5665ne-12232.gst.fits'

#------------------------------------------------------
# Artificial Star Test Input File Generation Parameters
#------------------------------------------------------

# ast_models_selected_per_age : integer
# Number of models to pick per age (Default = 70).
ast_models_selected_per_age = 70  # NOT USED in flux bin method

# ast_bands_above_maglimit : integer 
# Number of filters that must be above the magnitude limit
# for an AST to be included in the list (Default = 3)
ast_bands_above_maglimit = 3  # NOT USED in flux bin method

# ast_n_flux_bins : integer
# The number of flux bins into which the dynamic range of the
# model grid in each filter is divided
ast_n_flux_bins = 40

# ast_n_per_flux_bin : integer
# Minimum number of model seds that need to fall into each bin
ast_n_per_flux_bin = 50

# ast_realization_per_model : integer
# Number of Realizations of each included AST model
# to be put into the list. (Default = 20)
ast_realization_per_model = 1  # for the toothpick model (NOT truncheon)
                             

# ast_maglimit : float (single value or array with one value per filter)
# (1) option 1: [number] to change the number of mags fainter than
#                  the 90th percentile
#               faintest star in the photometry catalog to be used for
#                  the mag cut.
#               (Default = 1)
# (2) option 2: [space-separated list of numbers] to set custom faint end limits
#               (one value for each band).
ast_maglimit = [1.]  # NOT USED for this production run

# ast_with_positions :  (bool,optional)
# If True, the ast list is produced with X,Y positions.
# If False, the ast list is produced with only magnitudes.
ast_with_positions = True

# ast_density_table :  (string,optional)
# Name of density table created by
# tools/create_background_density_map.py, containing either the source
# density map or the background density map. If supplied, the ASTs will
# be repeated for each density bin in the table
ast_density_table = None
# ast_density_table = 'data/b15_4band_det_27_A_sourcedens_map.hd5'

#ast_N_bins : (int, optional)
#Number of source or background bins that you want ASTs repeated over
#ast_N_bins = 8

                         
# ast_pixel_distribution : float (optional)
# (Used if ast_with_positions is True), minimum pixel separation between AST
# position and catalog star used to determine the AST spatial distribution
ast_pixel_distribution = 10.0 

# ast_reference_image : string (optional, but required if ast_with_positions
# is True and no X and Y information  is present in the photometry catalog)	
# Name of the reference image used by DOLPHOT when running the measured 
# photometry.	            
ast_reference_image = None

# ast_coord_boundary : None, or list of two arrays (optional)
# If supplied, these RA/Dec coordinates will be used to limit the region
# over which ASTs are generated.  Input should be list of two arrays, the
# first RA and the second Dec, ordered sequentially around the region
# (either CW or CCW).
ast_coord_boundary = None


#-------------------------------------------
#Noise Model Artificial Star Test Parameters
#-------------------------------------------

# astfile : string
#   pathname of the AST files (single camera ASTs)
astfile = 'data/14675_LMC-5665ne-12232.gst.fake.fits'

# ast_colnames : list of strings 
#   names of columns for filters in the AST catalog (AC)
ast_colnames = np.array(basefilters)

# noisefile : string
#   create a name for the noise model
noisefile = project + '/' + project + '_noisemodel.hd5'

# absflux calibration covariance matrix for HST specific filters (AC)
absflux_a_matrix = absflux_covmat.hst_frac_matrix(filters)

# Distances: distance to the galaxy [min, max, step] or [fixed number]
distances = [18.5]

# Distance unit (any length or units.mag)
distance_unit = units.mag

# velocity of galaxy
velocity = 262.2 * units.km / units.s # LMC velocity from SIMBAD

################

### Stellar grid definition

# log10(Age) -- [min,max,step] to generate the isochrones in years
#   example [6.0, 10.13, 1.0]
logt = [6.0, 10.13, 0.1]

# note: Mass is not sampled, instead the isochrone supplied
#       mass spacing is used instead

# Metallicity : list of floats
#   Here: Z == Z_initial, NOT Z(t) surface abundance
#   PARSECv1.2S accepts values 1.e-4 < Z < 0.06
#   example z = [0.03, 0.019, 0.008, 0.004]
#   can they be set as [min, max, step]?
z = (10**np.array([-2.3, -2.0, -1.7, -1.4, -1.1, -0.8, -0.5, -0.2,  0.1])).tolist()

# Isochrone Model Grid
#   Current Choices: Padova or MIST
#   PadovaWeb() -- `modeltype` param for iso sets from ezpadova
#      (choices: parsec12s_r14, parsec12s, 2010, 2008, 2002)
#   MISTWeb() -- `rotation` param (choices: vvcrit0.0=default, vvcrit0.4)
#
# Default: PARSEC+CALIBRI
oiso = isochrone.PadovaWeb()
# Alternative: PARSEC1.2S -- old grid parameters
#oiso = isochrone.PadovaWeb(modeltype='parsec12s', filterPMS=True)
# Alternative: MIST -- v1, no rotation
#oiso = isochrone.MISTWeb()

# Stellar Atmospheres library definition
osl = stellib.Tlusty() + stellib.Kurucz()

################

### Dust extinction grid definition
extLaw = extLaw = extinction.Generalized_RvFALaw(ALaw=extinction.Generalized_DustExt(curve='F20'),
                                                 BLaw=extinction.Generalized_DustExt(curve='G03_SMCBar'))

# A(V): dust column in magnitudes
#   acceptable avs > 0.0
#   example [min, max, step] = [0.0, 10.055, 1.0]
avs = [0.01, 10.0, 0.05]
av_prior_model = {'name': 'flat'}
#av_prior_model = {'name': 'lognormal',
#                  'max_pos': 2.0,
#                  'sigma': 1.0,
#                  'N': 10.}

# R(V): dust average grain size
#   example [min, max, step] = [2.0,6.0,1.0]
rvs = [2.0,6.0,0.5]
rv_prior_model = {'name': 'flat'}
#rv_prior_model = {'name': 'lognormal',
#                  'max_pos': 2.0,
#                  'sigma': 1.0,
#                  'N': 10.}

# fA: mixture factor between "MW" and "SMCBar" extinction curves
#   example [min, max, step] = [0.0,1.0, 0.25]
fAs = [0.0,1.0, 0.2]
fA_prior_model = {'name': 'flat'}
#fA_prior_model = {'name': 'lognormal',
#                  'max_pos': 0.5,
#                  'sigma': 0.2,
#                  'N': 10.}

################

# add in the standard filters to enable output of stats and pdf1d values
# for the observed fitlers (AC)
add_spectral_properties_kwargs = dict(filternames=filters)

################
# The following code does not require user's attention (AC)
################

class GenFluxCatalog(Observations):
    """Generic n band filter photometry
    This class implements a direct access to the Generic HST measured fluxes.

    ..note::
        it does not implement uncertainties as in this model, the noise is
        given through artificial star tests
    """
    def __init__(self, inputFile, filters=filters):
        """ Construct the interface """
        desc = 'GENERIC star: %s' % inputFile
        Observations.__init__(self, inputFile, desc=desc)
        self.setFilters( filters )
        #some bad values smaller than expected
        # in physical flux units
        self.setBadValue(6e-40)

        # rate column needed as this is the *flux* column
        for ik,k in enumerate(filters):
            self.data.set_alias(k, obs_colnames[ik])

    def getFlux(self, num, units=False):
        """returns the absolute flux of an observation 

        Parameters
        ----------
        num: int
            index of the star in the catalog to get measurement from

        units: bool
            if set returns the fluxes with a unit capsule

        Returns
        -------
        flux: ndarray[dtype=float, ndim=1]
            Measured integrated flux values throughout the filters 
            in erg/s/cm^2/A
        """

        # case for using '_flux' result
        d = self.data[num]
        
        flux = np.array([ d[self.data.resolve_alias(ok)] 
                          for ok in self.filters ]) * self.vega_flux
        
        if units is True:
            return flux * units.erg / (units.s*units.cm*units.cm*units.angstrom)
        else:
            return flux

    def setFilters(self, filters):
        """ set the filters and update the vega reference for the conversions

        Parameters
        ----------
        filters: sequence
            list of filters using the internally normalized namings
        """
        self.filters = filters

        #Data "rates" are normalized to Vega already, fits are not using vega

        # for optimization purpose: pre-compute
        #   getting vega mags, require to open and read the content of one file.
        #   since getObs, calls getFlux, for each star you need to do this
        #   expensive operation
        with Vega() as v:
            _, vega_flux, _ = v.getFlux(filters)

        self.vega_flux = vega_flux


def get_obscat(obsfile=obsfile, filters=filters, *args, **kwargs):
    """ Function that generates a data catalog object with the correct
    arguments

    Parameters
    ----------
    obsfile: str, optional (default datamodel.obsfile)
        observation file

    filters: sequence(str), optional, datamodel.filters
        seaquence of filters of the data

    returns
    -------
    obs: GenFluxCatalog
        observation catalog
    """
    obs = GenFluxCatalog(obsfile, filters=filters)
    return obs
