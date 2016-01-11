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
uncertainty in the efficiency value was too large (larger than half the value), *the corresponding
efficiency was set to zero in the SModelS database*. The purpose of this is to avoid points with large uncertainties
and produce a more conservative efficiency map.
However, as a result, some points will have smaller efficiencies in SModelS than the ones used in Fastlim.
