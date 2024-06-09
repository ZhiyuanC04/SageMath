# sage_setup: distribution = sagemath-categories
r"""
Kac-Moody Algebras With Triangular Decomposition Basis

AUTHORS:

- Travis Scrimshaw (07-15-2017): Initial implementation
"""

# ****************************************************************************
#       Copyright (C) 2017 Travis Scrimshaw <tcscrims at gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  https://www.gnu.org/licenses/
# ****************************************************************************

from sage.misc.abstract_method import abstract_method
from sage.misc.cachefunc import cached_method
from sage.categories.category_types import Category_over_base_ring
from sage.categories.kac_moody_algebras import KacMoodyAlgebras


class TriangularKacMoodyAlgebras(Category_over_base_ring):
    """
    Category of Kac-Moody algebras with a distinguished basis that
    respects the triangular decomposition.

    We require that the grading group is the root lattice of the
    appropriate Cartan type.
    """
    @cached_method
    def super_categories(self):
        """
        EXAMPLES::

            sage: from sage.categories.triangular_kac_moody_algebras import TriangularKacMoodyAlgebras
            sage: TriangularKacMoodyAlgebras(QQ).super_categories()
            [Join of Category of graded Lie algebras with basis over Rational Field
                 and Category of kac moody algebras over Rational Field]

        """
        # We do not also derive from (Magmatic) algebras since we don't want *
        #   to be our Lie bracket
        # Also this doesn't inherit the ability to add axioms like Associative
        #   and Unital, both of which do not make sense for Lie algebras
        return [KacMoodyAlgebras(self.base_ring()).WithBasis().Graded()]

    class ParentMethods:
        def _part_on_basis(self, m):
            """
            Return whether the basis element indexed by ``m`` is
            in the lower, zero, or upper part of ``self``.

            OUTPUT:

            `-1` if ``m`` is a negative root, `0` if zero, or `1`
            if ``m`` is a positive root

            EXAMPLES::

                sage: L = lie_algebras.so(QQ, 5)                                        # needs sage.combinat sage.modules
                sage: L.f()                                                             # needs sage.combinat sage.modules
                Finite family {1: E[-alpha[1]], 2: E[-alpha[2]]}
                sage: L.f(1)                                                            # needs sage.combinat sage.modules
                E[-alpha[1]]
            """
            deg = self.degree_on_basis(m)
            if not deg:
                return 0
            return 1 if deg.is_positive_root() else -1

        @cached_method
        def _part_generators(self, positive=False):
            r"""
            Return the Lie algebra generators for the positive or
            negative half of ``self``.

            .. NOTE::

                If the positive/negative generators correspond to the
                generators with (negative) simple roots, then this method
                will find them. If they do not, then this method *must*
                be overwritten. One should also overwrite this method in
                object classes when there is a better method to obtain them.
                Furthermore, this assumes that :meth:`lie_algebra_generators`
                is a finite set.

            INPUT:

            - ``positive`` -- boolean (default: ``False``); if ``True``
              then return positive part generators, otherwise the return
              the negative part generators

            OUTPUT:

            A :func:`~sage.sets.family.Family` whose keys are the
            index set of ``self``.

            EXAMPLES::

                sage: L = LieAlgebra(QQ, cartan_type=['E', 6])                          # needs sage.combinat sage.modules
                sage: list(L._part_generators(False))                                   # needs sage.combinat sage.modules
                [E[-alpha[1]], E[-alpha[2]], E[-alpha[3]],
                 E[-alpha[4]], E[-alpha[5]], E[-alpha[6]]]
            """
            I = self._cartan_type.index_set()
            P = self._cartan_type.root_system().root_lattice()
            ali = P.simple_roots().inverse_family()
            if positive:
                d = {ali[g.degree()]: g for g in self.lie_algebra_generators()
                     if self._part(g) > 0}
            if not positive:
                d = {ali[-g.degree()]: g for g in self.lie_algebra_generators()
                     if self._part(g) < 0}
            from sage.sets.family import Family
            return Family(I, d.__getitem__)

        def e(self, i=None):
            """
            Return the generators `e` of ``self``.

            INPUT:

            - ``i`` -- (optional) if specified, return just the
              generator `e_i`

            EXAMPLES::

                sage: L = lie_algebras.so(QQ, 5)                                        # needs sage.combinat sage.modules
                sage: L.e()                                                             # needs sage.combinat sage.modules
                Finite family {1: E[alpha[1]], 2: E[alpha[2]]}
                sage: L.e(1)                                                            # needs sage.combinat sage.modules
                E[alpha[1]]
            """
            E = self._part_generators(True)
            if i is None:
                return E
            return E[i]

        def f(self, i=None):
            """
            Return the generators `f` of ``self``.

            INPUT:

            - ``i`` -- (optional) if specified, return just the
              generator `f_i`

            EXAMPLES::

                sage: L = lie_algebras.so(QQ, 5)                                        # needs sage.combinat sage.modules
                sage: L.f()                                                             # needs sage.combinat sage.modules
                Finite family {1: E[-alpha[1]], 2: E[-alpha[2]]}
                sage: L.f(1)                                                            # needs sage.combinat sage.modules
                E[-alpha[1]]
            """
            F = self._part_generators(False)
            if i is None:
                return F
            return F[i]

        @abstract_method
        def _negative_half_index_set(self):
            """
            Return an indexing set for the negative half of ``self``.

            EXAMPLES::

                sage: L = lie_algebras.so(QQ, 5)                                        # needs sage.combinat sage.modules
                sage: L._negative_half_index_set()                                      # needs sage.combinat sage.modules
                [-alpha[2], -alpha[1], -alpha[1] - alpha[2],
                 -alpha[1] - 2*alpha[2]]
            """

        @abstract_method
        def _weight_action(self, m, wt):
            """
            Return the action of the basis element indexed by ``m`` on ``wt``.

            INPUT:

            - ``m`` -- an index of a basis element of the Cartan subalgebra
            - ``wt`` -- a weight

            EXAMPLES::

                sage: # needs sage.combinat sage.modules
                sage: L = lie_algebras.sp(QQ, 6)
                sage: La = L.cartan_type().root_system().weight_space().fundamental_weights()
                sage: mu = La[1] - 3/5*La[2]
                sage: ac = L.cartan_type().root_system().coroot_lattice().simple_roots()
                sage: L._weight_action(ac[1], mu)
                1
                sage: L._weight_action(ac[2], mu)
                -3/5
                sage: L._weight_action(ac[3], mu)
                0
            """

        def verma_module(self, la, basis_key=None, **kwds):
            """
            Return the Verma module with highest weight ``la``
            over ``self``.

            INPUT:

            - ``basis_key`` -- (optional) a key function for the indexing
              set of the basis elements of ``self``

            EXAMPLES::

                sage: # needs sage.combinat sage.modules
                sage: L = lie_algebras.sl(QQ, 3)
                sage: P = L.cartan_type().root_system().weight_lattice()
                sage: La = P.fundamental_weights()
                sage: M = L.verma_module(La[1] + La[2])
                sage: M
                Verma module with highest weight Lambda[1] + Lambda[2]
                 of Lie algebra of ['A', 2] in the Chevalley basis
            """
            from sage.algebras.lie_algebras.verma_module import VermaModule
            return VermaModule(self, la, basis_key=basis_key, **kwds)

    class ElementMethods:
        def part(self):
            """
            Return whether the element ``v`` is in the lower,
            zero, or upper part of ``self``.

            OUTPUT:

            `-1` if ``v`` is in the lower part, `0` if in the
            zero part, or `1` if in the upper part

            EXAMPLES::

                sage: # needs sage.combinat sage.modules
                sage: L = LieAlgebra(QQ, cartan_type='F4')
                sage: L.inject_variables()
                Defining e1, e2, e3, e4, f1, f2, f3, f4, h1, h2, h3, h4
                sage: e1.part()
                1
                sage: f4.part()
                -1
                sage: (h2 + h3).part()
                0
                sage: (f1.bracket(f2) + 4*f4).part()
                -1
                sage: (e1 + f1).part()
                Traceback (most recent call last):
                ...
                ValueError: element is not in one part
            """
            P = self.parent()
            S = [P._part_on_basis(m) for m in self.support()]
            if all(k < 0 for k in S):
                return -1
            if all(k > 0 for k in S):
                return 1
            if all(k == 0 for k in S):
                return 0
            raise ValueError("element is not in one part")
