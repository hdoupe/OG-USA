import os
import sys
import pytest
import tempfile
import pickle
import numpy as np
import pandas as pd
from ogusa.utils import comp_array
from ogusa.utils import comp_scalar
from ogusa.utils import dict_compare
from ogusa.get_micro_data import get_calculator
from ogusa import SS
from ogusa import TPI
import uuid
import time

from ogusa.scripts import postprocess
from ogusa.scripts.execute import runner
from ogusa.scripts.execute_funcs import get_sim_params, solve_SS, solve_TPI
SS.ENFORCE_SOLUTION_CHECKS = False
TPI.ENFORCE_SOLUTION_CHECKS = False

def run_micro_macro(reform, user_params, guid, **kwargs):

    guid = ''
    start_time = time.time()

    REFORM_DIR = "./OUTPUT_REFORM_" + guid
    BASELINE_DIR = "./OUTPUT_BASELINE_" + guid

    # Add start year from reform to user parameters
    start_year = sorted(reform.keys())[0]
    user_params['start_year'] = start_year

    with open("log_{}.log".format(guid), 'w') as f:
        f.write("guid: {}\n".format(guid))
        f.write("reform: {}\n".format(reform))
        f.write("user_params: {}\n".format(user_params))


    '''
    ------------------------------------------------------------------------
        Run baseline
    ------------------------------------------------------------------------
    '''
    output_base = BASELINE_DIR
    kwargs.update({'output_base':output_base, 'baseline_dir':BASELINE_DIR, 'test':True,
                   'time_path':True, 'baseline':True, 'analytical_mtrs':False,
                   'user_params':user_params, 'age_specific':False, 'run_micro':False,
                   'guid':guid})
    baseline_sim_params, baseline_ss_output, baseline_tpi_output, baseline_macro_output = runner(**kwargs)

    '''
    ------------------------------------------------------------------------
        Run reform
    ------------------------------------------------------------------------
    '''

    output_base = REFORM_DIR
    kwargs.update({'output_base':output_base, 'baseline_dir':BASELINE_DIR,
                   'test':True, 'time_path':True, 'baseline':False,
                   'analytical_mtrs':False, 'reform':reform, 'user_params':user_params,
                   'age_specific':False, 'guid': guid, 'run_micro':False})
    reform_sim_params, reform_ss_output, reform_tpi_output, reform_macro_output = runner(**kwargs)

    time.sleep(0.5)
    ans = postprocess.create_diff(baseline_dir=BASELINE_DIR, policy_dir=REFORM_DIR)
    print "total time was ", (time.time() - start_time)

    return (baseline_sim_params, baseline_ss_output, baseline_tpi_output, baseline_macro_output,
            reform_sim_params, reform_ss_output, reform_tpi_output, reform_macro_output)

def run_funcs_micro_macro(reform, user_params, guid, **kwargs):

    guid = ''
    start_time = time.time()

    REFORM_DIR = "./OUTPUT_REFORM_" + guid
    BASELINE_DIR = "./OUTPUT_BASELINE_" + guid

    # Add start year from reform to user parameters
    start_year = sorted(reform.keys())[0]
    user_params['start_year'] = start_year

    with open("log_{}.log".format(guid), 'w') as f:
        f.write("guid: {}\n".format(guid))
        f.write("reform: {}\n".format(reform))
        f.write("user_params: {}\n".format(user_params))


    '''
    ------------------------------------------------------------------------
        Run baseline
    ------------------------------------------------------------------------
    '''
    output_base = BASELINE_DIR
    kwargs.update({'output_base':output_base, 'baseline_dir':BASELINE_DIR, 'test':True,
                   'time_path':True, 'baseline':True, 'analytical_mtrs':False,
                   'user_params':user_params, 'age_specific':False, 'run_micro':False,
                   'guid':guid})

    baseline_sim_params = get_sim_params(**kwargs)
    baseline_sim_params, baseline_ss_output = solve_SS(**baseline_sim_params)
    baseline_tpi_output, baseline_macro_output = solve_TPI(**baseline_sim_params)

    '''
    ------------------------------------------------------------------------
        Run reform
    ------------------------------------------------------------------------
    '''

    output_base = REFORM_DIR
    kwargs.update({'output_base':output_base, 'baseline_dir':BASELINE_DIR,
                   'test':True, 'time_path':True, 'baseline':False,
                   'analytical_mtrs':False, 'reform':reform, 'user_params':user_params,
                   'age_specific':False, 'guid': guid, 'run_micro':False})
    reform_sim_params = get_sim_params(**kwargs)
    reform_sim_params, reform_ss_output = solve_SS(**reform_sim_params)
    reform_tpi_output, reform_macro_output = solve_TPI(**reform_sim_params)

    # time.sleep(0.5)
    # ans = postprocess.create_diff(baseline_dir=BASELINE_DIR, policy_dir=REFORM_DIR)
    # print "total time was ", (time.time() - start_time)

    return (baseline_sim_params, baseline_ss_output, baseline_tpi_output, baseline_macro_output,
            reform_sim_params, reform_ss_output, reform_tpi_output, reform_macro_output)


def test_run_micro_macro():

    reform = {
    2017: {
        '_II_rt1': [.09],
        '_II_rt2': [.135],
        '_II_rt3': [.225],
        '_II_rt4': [.252],
        '_II_rt5': [.297],
        '_II_rt6': [.315],
        '_II_rt7': [0.3564],
    }, }
    kwargs = {"baseline_spending": True}
    (func_baseline_sim_params, func_baseline_ss_output, func_baseline_tpi_output, func_baseline_macro_output,
        func_reform_sim_params, func_reform_ss_output, func_reform_tpi_output, func_reform_macro_output) = \
        run_funcs_micro_macro(reform,
                              user_params={'frisch': 0.44,
                                           'g_y_annual': 0.021},
                              guid='abc', **kwargs)

    (baseline_sim_params, baseline_ss_output, baseline_tpi_output, baseline_macro_output,
        reform_sim_params, reform_ss_output, reform_tpi_output, reform_macro_output) = \
            run_micro_macro(reform=reform,
                            user_params={'frisch': 0.44, 'g_y_annual': 0.021},
                            guid='abc', **kwargs)


    # remove key, value pair where value is a function.  numpy cannot
    # compare equality of interp1d functions
    # assert that x, y values are equal
    func_interp = func_baseline_sim_params["run_params"].pop("chi_n_interp")
    interp = baseline_sim_params["run_params"].pop("chi_n_interp")
    np.allclose(func_interp(func_interp.x), interp(interp.x))

    func_interp = func_reform_sim_params["run_params"].pop("chi_n_interp")
    interp = reform_sim_params["run_params"].pop("chi_n_interp")
    np.allclose(func_interp(func_interp.x), interp(interp.x))

    # assert_equal tests equality of dictionaries and numpy arrays
    np.testing.assert_equal(func_baseline_sim_params, baseline_sim_params)
    np.testing.assert_equal(func_baseline_ss_output, baseline_ss_output)
    np.testing.assert_equal(func_baseline_tpi_output, baseline_tpi_output)
    np.testing.assert_equal(func_baseline_macro_output, baseline_macro_output)

    np.testing.assert_equal(func_reform_sim_params, reform_sim_params)
    np.testing.assert_equal(func_reform_ss_output, reform_ss_output)
    np.testing.assert_equal(func_reform_tpi_output, reform_tpi_output)
    np.testing.assert_equal(func_reform_macro_output, reform_macro_output)
