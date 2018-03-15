import json
import os
import collections as collect
import six

from taxcalc.parameters import ParametersBase
from taxcalc.growfactors import Growfactors
from taxcalc.policy import Policy

import ogusa

class ParametersBaseOGUSA(ParametersBase):
    """
    Quick fix so that the path pulled from __file__ is relative to this file
    and not the `ParametersBase` file located int he conda installation path

    This allows us to read the `ogusa/default_parameters.json` file
    """

    @classmethod
    def _params_dict_from_json_file(cls):
        """
        Read DEFAULTS_FILENAME file and return complete dictionary.

        Parameters
        ----------
        nothing: void

        Returns
        -------
        params: dictionary
            containing complete contents of DEFAULTS_FILENAME file.
        """
        if cls.DEFAULTS_FILENAME is None:
            msg = 'DEFAULTS_FILENAME must be overridden by inheriting class'
            raise NotImplementedError(msg)
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            cls.DEFAULTS_FILENAME)
        if os.path.exists(path):
            with open(path) as pfile:
                params_dict = json.load(pfile,
                                        object_pairs_hook=collect.OrderedDict)
        else:
            # cannot call read_egg_ function in unit tests
            params_dict = read_egg_json(
                cls.DEFAULTS_FILENAME)  # pragma: no cover
        return params_dict

    def set_default_vals(self, known_years=999999):
        """
        Called by initialize method and from some subclass methods.
        """
        if hasattr(self, '_vals'):
            for name, data in self._vals.items():
                if not isinstance(name, six.string_types):
                    msg = 'parameter name {} is not a string'
                    raise ValueError(msg.format(name))
                integer_values = data.get('integer_value', None)
                values = data.get('value', None)
                if values:
                    # removed parameter extension from start year to end of
                    # budget window. Currently this stores the default value
                    # as a list object of length 1
                    setattr(self, name, values)
        self.set_year(self._start_year)


class Specs(ParametersBaseOGUSA):
    DEFAULTS_FILENAME = 'default_parameters.json'
    JSON_START_YEAR = 2013  # remains the same unless earlier data added
    LAST_KNOWN_YEAR = 2017  # last year for which indexed param vals are known
    LAST_BUDGET_YEAR = 2027  # increases by one every calendar year
    DEFAULT_NUM_YEARS = LAST_BUDGET_YEAR - JSON_START_YEAR + 1

    def __init__(self,
                 start_year=JSON_START_YEAR,
                 num_years=DEFAULT_NUM_YEARS,
                 initial_estimates=False):
        super(Specs, self).__init__()

        # reads in default data
        self._vals = self._params_dict_from_json_file()

        if num_years < 1:
            raise ValueError('num_years cannot be less than one')

        # does cheap calculations such as growth
        self.initialize(start_year, num_years, initial_estimates=False)

        self.reform_warnings = ''
        self.reform_errors = ''
        self._ignore_errors = False

    def initialize(self, start_year, num_years, initial_estimates=False):
        """
        ParametersBase reads JSON file and sets attributes to self
        Next call self.ogusa_set_default_vals for further initialization
        If estimate_params is true, then run long running estimation routines
        """
        super(Specs, self).initialize(start_year, num_years)
        self.ogusa_set_default_vals()
        if initial_estimates:
            self.estimate_parameters()

    def ogusa_set_default_vals(self):
        """
        Does cheap calculations such as calculating/applying growth rates
        """
        self.b_ellipse, self.upsilon = ogusa.elliptical_u_est.estimation(
            self.frisch[0],
            self.ltilde[0]
        )
        # call some more functions

    def esitimate_parameters(self, data=None, reform={}):
        """
        Runs long running parameter estimatation routines such as estimating
        tax function parameters
        """
        # self.tax_func_estimate = tax_func_estimate(self.BW, self.S, self.starting_age, self.ending_age,
        #                                 self.start_year, self.baseline,
        #                                 self.analytical_mtrs, self.age_specific,
        #                                 reform=None, data=data)
        pass


    def implement_reform(self, specs):
        """
        Follows Policy.implement_reform

        This is INCOMPLETE and needs to be filled in. This is the place
        to call parameter validating functions
        """

        self._validate_parameter_names_types(specs)
        if not self._ignore_errors and self.reform_errors:
            raise ValueError(self.reform_errors)

        self._validate_parameter_values(reform_parameters)

        raise NotImplementedError()

    def read_json_parameters_object(self, parameters):
        raise NotImplementedError()

    def _validate_parameter_names_types(self, reform):
        """
        hopefully can use taxcalc.Policy._validate_parameter_values here
        """
        raise NotImplementedError()

    def _validate_parameter_values(self, parameters_set):
        """
        hopefully can use taxcalc.Policy._validate_parameter_values here
        """
        raise NotImplementedError()


# copied from taxcalc.tbi.tbi.reform_errors_warnings--probably needs further
# changes
def reform_warnings_errors(user_mods):
    """
    The reform_warnings_errors function assumes user_mods is a dictionary
    returned by the Calculator.read_json_param_objects() function.

    This function returns a dictionary containing two STR:STR pairs:
    {'warnings': '<empty-or-message(s)>', 'errors': '<empty-or-message(s)>'}
    In each pair the second string is empty if there are no messages.
    Any returned messages are generated using current_law_policy.json
    information on known policy parameter names and parameter value ranges.

    Note that this function will return one or more error messages if
    the user_mods['policy'] dictionary contains any unknown policy
    parameter names or if any *_cpi parameters have values other than
    True or False.  These situations prevent implementing the policy
    reform specified in user_mods, and therefore, no range-related
    warnings or errors will be returned in this case.
    """
    rtn_dict = {'warnings': '', 'errors': ''}

    # create Policy object and implement reform
    pol = Policy()
    try:
        pol.implement_reform(user_mods['policy'])
        rtn_dict['warnings'] = pol.reform_warnings
        rtn_dict['errors'] = pol.reform_errors
    except ValueError as valerr_msg:
        rtn_dict['errors'] = valerr_msg.__str__()
    return rtn_dict

if __name__ == '__main__':
    specs = Specs()
    print(specs.__dict__)
