Main Issues
-----------

Some of main differences between SModelS and Fastlim are:


SMS Mapping
~~~~~~~~~~~

SModelS neglects detailed information about the simplified models, such as spin, color charge, etc. On the other hand, Fastlim considers most of this information and its topologies refer to specific SUSY processes. In order to understand the implications of the two different approaches, consider the two processes below:

.. math::
	\tilde{g} + \tilde{g} & \rightarrow (g \tilde{\chi}_1^{0}) + (g \tilde{\chi}_1^{0}) \\
	\tilde{q} + \tilde{q} & \rightarrow (q \tilde{\chi}_1^{0}) + (q \tilde{\chi}_1^{0})

In the Fastlim approach both processes are distinct (the first is labeled  **GgN1_GgN1** while the second
would be **QqN1_QqN1**), while in SModelS both processes are mapped to  **T2** (or *[[[jet]],[[jet]]]*).
Furthermore, *in the current version Fastlim only has efficiency maps for*  **GgN1_GgN1**.


Now consider a model where both processes are present. In this case Fastlim will only consider the contribution from
**GgN1_GgN1**, since there are no maps for  **QqN1_QqN1**.
On the other hand, SModelS will use Fastlim efficiency maps for **GgN1_GgN1** and apply the efficiencies for the two
processes, since within the SModelS philosophy both are identical to **T2**. As a result, the theoretical prediction
from SModelS will be larger than in Fastlim, due
to a larger coverage of the topologies.


**Obs:** In order to avoid this issue, it is possible to distinguish between gluon-jets and quark-jets in SModelS. This can
be implemented by removing gluons ("g") from the jet definition in particles.py. Furthermore the
efficiency maps (or UL maps) which refer to gluon jets would have to be modified. First a new TxName would have to be
created (distinct from T2) and the constraint would have to be changed (:math:`[[[jet]],[[jet]]] \rightarrow [[[g]],[[g]]]`).


Efficiency Maps
~~~~~~~~~~~~~~~

The efficiency maps in the SModelS database are identical to the ones in Fastlim, except
for an important difference. When translating Fastlim maps to the SModelS database, whenever the
uncertainty in the efficiency value is larger than 25%, *the corresponding
efficiency was set to zero in the SModelS database*. The purpose of this is to avoid points with large uncertainties
and produce a more conservative efficiency map.
However, as a result, some points will have smaller efficiencies in SModelS than the ones used in Fastlim.

Furthermore, Fastlim uses a linear interpolation for the logarithm of the efficiencies, where SModelS
interpolates directly on the efficiency values. In most cases the differences between the two
methods are negligible, except in regions of parameter space where there is a sharp drop on the efficiencies. 



Cross-Sections
~~~~~~~~~~~~~~

Fastlim uses its own tables of cross-sections based on arxiv:1206.2892.
On the other hand SModelS uses Pythia6 and NLLfast to compute cross-sections.
Usuallly the cross-section values are very similar with only a few percent difference.
For the case of gluino pair production, however, the transition to the decoupled squark regime
in Fastlim sometimes occurs for too low squark masses, when they have not really decoupled yet.
As an specific example, consider the point :math:`(m_{\tilde{g}},m_{\tilde{q}}) = (1285 \mbox{GeV},2.5 \mbox{TeV})`.
The quoted 8 TeV cross-section for this point given by Fastlim is:

.. math::
   \sigma_{\tilde{g} \tilde{g}}^{NLO+NLL} = 2.17 fb
   
While NLLfast gives:

.. math::
   \sigma_{\tilde{g} \tilde{g}}^{NLO+NLL} = 1.60 fb      

If we ask NLLfast to compute this cross-section in the decoupled regime we obtain:

.. math::
   \sigma_{\tilde{g} \tilde{g}}^{NLO+NLL} = 2.18 fb \; \mbox{ (decoupled squarks)}

Hence we can clearly see that the Fastlim cross-section assumes decoupled squarks when 
they have not fully decoupled yet.
In this case results obtained from Fastlim can significantly differ from SModelS.


Invisible and Mass Compression
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The invisible compression feature is not included in Fastlim. Hence it must be turned off
before a proper comparison with SModelS can be made.
Furthermore, the mass compression implemented in Fastlim only acts on Chargino 1 and Neutralinos 1 and 2
(the minimum mass gap in Fastlim is 10 GeV).
Other sparticles are not automatically compressed. Therefore in some cases the SModelS predictions
may become larger than the ones obtained with Fastlim.
