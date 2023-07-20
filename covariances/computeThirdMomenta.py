"""
Hi Wolfgang,

The third moment can be derived from the upper and lower uncertainties in the
N^pred_SR columns of Tables 4 and 5 in the paper. These are extracted from
Figure 10 as the "Results" table in HEPData Here is the code snippet I
use for this:
"""

def moment3(sigHi, sigLo):
    # Compute 3rd moment of bkg pdf from the upper, lower uncertainties
    from scipy import stats as st
    from scipy import integrate as integr
    def x3_times_bifurgauss(x, sigHi, sigLo):
      if x >= 0:
        return x*x*x * 2*sigHi/(sigLo + sigHi) * st.norm.pdf(x, 0, sigHi)
      else:
        return x*x*x * 2*sigLo/(sigLo + sigHi) * st.norm.pdf(x, 0, sigLo)
    m3, err = integr.quad(x3_times_bifurgauss, -np.inf, np.inf, args = (sigHi, sigLo))
    return m3
