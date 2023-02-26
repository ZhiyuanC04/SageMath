# -*- coding: utf-8 -*-
r"""
Integer-valued polynomial rings

AUTHORS:

- Frédéric Chapoton (2013-03): Initial version
"""
# ***************************************************************************
#  Copyright (C) 2013 Frédéric Chapoton
#
#  Distributed under the terms of the GNU General Public License (GPL)
#                  https://www.gnu.org/licenses/
# ***************************************************************************
from sage.arith.misc import (binomial, factorial)
from sage.categories.rings import Rings
from sage.categories.all import Algebras
from sage.categories.realizations import Category_realization_of_parent
from sage.combinat.free_module import CombinatorialFreeModule
from sage.matrix.constructor import matrix
from sage.misc.cachefunc import cached_method
from sage.modules.free_module_element import vector
from sage.rings.integer import Integer
from sage.rings.integer_ring import ZZ
from sage.rings.polynomial.polynomial_ring import polygen
from sage.rings.polynomial.polynomial_ring_constructor import PolynomialRing
from sage.rings.rational_field import QQ
from sage.sets.non_negative_integers import NonNegativeIntegers
from sage.sets.family import Family
from sage.misc.bindable_class import BindableClass
from sage.structure.unique_representation import UniqueRepresentation
from sage.structure.parent import Parent


class IntegerValuedPolynomialRing(UniqueRepresentation, Parent):
    r"""
    The integer-valued polynomial ring over a base ring.

    Integer-valued polynomial rings are commutative and associative
    algebras, with a basis indexed by non-negative integers.

    There are two natural bases, made of the sequence
    `\binom{x}{n}` for `n \geq 0` (the *binomial basis*) and of
    the other sequence `\binom{x+n}{n}` for `n \geq 0` (the *shifted basis*).

    TESTS::

        sage: IntegerValuedPolynomialRing(24)
        Traceback (most recent call last):
        ...
        TypeError: argument R must be a commutative ring
    """
    def __init__(self, R):
        if R not in Rings().Commutative():
            raise TypeError("argument R must be a commutative ring")
        self._base = R
        cat = Algebras(R).Commutative().WithBasis()
        Parent.__init__(self, base=R, category=cat.WithRealizations())

        S = self.S()
        B = self.B()
        B.module_morphism(S._from_binomial_basis, codomain=S).register_as_coercion()
        S.module_morphism(B._from_shifted_basis, codomain=B).register_as_coercion()

    _shorthands = ["B", "S"]

    def a_realization(self):
        r"""
        Return the default realization of ``self``.

        This is the shifted basis.

        EXAMPLES::

            sage: A = IntegerValuedPolynomialRing(QQ)
            sage: A.a_realization()
            Integer-Valued Polynomial Ring over Rational Field
            in the shifted basis
        """
        return self.S()

    def indices(self):
        r"""
        Return the objects that index the basis elements of this algebra.

        This is the set `\NN` of nonnegative integers.

        EXAMPLES::

            sage: A = IntegerValuedPolynomialRing(QQ)
            sage: A.indices()
            Non negative integers
        """
        return NonNegativeIntegers()

    def _repr_(self) -> str:
        r"""
        Return the string representation.

        EXAMPLES::

            sage: IntegerValuedPolynomialRing(QQ)
            Integer-Valued Polynomial Ring over Rational Field
        """
        br = self.base_ring()
        return f"Integer-Valued Polynomial Ring over {br}"

    class Bases(Category_realization_of_parent):
        def super_categories(self) -> list:
            r"""
            Return the super-categories of ``self``.

            EXAMPLES::

                sage: A = IntegerValuedPolynomialRing(QQ); A
                Integer-Valued Polynomial Ring over Rational Field
                sage: C = A.Bases(); C
                Category of bases of Integer-Valued Polynomial Ring
                over Rational Field
                sage: C.super_categories()
                [Category of realizations of Integer-Valued Polynomial Ring
                 over Rational Field,
                 Join of Category of algebras with basis over Rational Field and
                 Category of filtered algebras over Rational Field and
                 Category of commutative algebras over Rational Field and
                 Category of realizations of unital magmas]
            """
            A = self.base()
            category = Algebras(A.base_ring()).Commutative().Filtered()
            return [A.Realizations(),
                    category.Realizations().WithBasis()]

        class ParentMethods:
            def _repr_(self) -> str:
                r"""
                EXAMPLES::

                    sage: F = IntegerValuedPolynomialRing(QQ).S()
                    sage: F  # indirect doctest
                    Integer-Valued Polynomial Ring over Rational Field
                    in the shifted basis
                    sage: F = IntegerValuedPolynomialRing(QQ).B()
                    sage: F  # indirect doctest
                    Integer-Valued Polynomial Ring over Rational Field
                    in the binomial basis
                """
                real = self.realization_of()
                return f"{real} in the {self._realization_name()} basis"

            @cached_method
            def one_basis(self):
                r"""
                Return the number 0, which index the unit of this algebra.

                EXAMPLES::

                    sage: A = IntegerValuedPolynomialRing(QQ).S()
                    sage: A.one_basis()
                    0
                    sage: A.one()
                    S[0]
                """
                return self.basis().keys()(0)

            def degree_on_basis(self, m):
                r"""
                Return the degree of the basis element indexed by ``m``.

                EXAMPLES::

                    sage: A = IntegerValuedPolynomialRing(QQ).S()
                    sage: A.degree_on_basis(4)  # indirect doctest
                    4
                """
                return ZZ(m)

            def gen(self):
                r"""
                Return the generator of this algebra.

                EXAMPLES::

                    sage: F = IntegerValuedPolynomialRing(ZZ).B()
                    sage: F.gen()
                    B[1]
                """
                return self.algebra_generators()[0]

            @cached_method
            def algebra_generators(self):
                r"""
                Return the generators of this algebra.

                EXAMPLES::

                    sage: A = IntegerValuedPolynomialRing(ZZ).S(); A
                    Integer-Valued Polynomial Ring over Integer Ring
                    in the shifted basis
                    sage: A.algebra_generators()
                    Family (S[1],)
                """
                NonNeg = self.basis().keys()
                return Family([self.monomial(NonNeg(1))])

            gens = algebra_generators

        class ElementMethods:
            def __call__(self, v):
                """
                Evaluation at some value ``v``

                EXAMPLES::

                     sage: F = IntegerValuedPolynomialRing(ZZ).S()
                     sage: B = F.gen()
                     sage: f = B**2+4*B+6
                     sage: f(1/3)
                     118/9

                     sage: F = IntegerValuedPolynomialRing(ZZ).B()
                     sage: B = F.gen()
                     sage: f = B**2+4*B+6
                     sage: f(1/3)
                     67/9
                """
                return self.polynomial()(v)

            def shift(self, j=1):
                """
                Shift all indices by `j`.

                INPUT:

                - `j` -- integer (default: 1)

                In the binomial basis, the shift by 1 corresponds to
                a summation operator from `0` to `x`.

                EXAMPLES::

                    sage: F = IntegerValuedPolynomialRing(ZZ).B()
                    sage: B = F.gen()
                    sage: (B+1).shift()
                    B[1] + B[2]
                    sage: (B+1).shift(3)
                    B[3] + B[4]
                """
                A = self.parent()
                return A._from_dict({i + j: c for i, c in self})

    class Shifted(CombinatorialFreeModule, BindableClass):
        r"""
        The integer-valued polynomial ring in the shifted basis.

        Integer-valued polynomial rings are commutative and associative
        algebras, with a basis indexed by non-negative integers.

        The basis used here is given by `B[i] = \binom{i+n}{i}` for `i \in \NN`.

        Assuming `n_1 \leq n_2`, the product of two monomials `B[n_1] \cdot B[n_2]`
        is given by the sum

        .. MATH::

            \sum_{k=0}^{n_1} (-1)^k \binom{n_1}{k}\binom{n_1+n_2-k}{n_1} B[n_1 + n_2 - k].

        There is a conversion formula between the two bases

        .. MATH::

            \binom{x}{i} = \sum_{k=0}^{i} (-1)^{i-k} \binom{i}{k} \binom{x+k}{k}.


        REFERENCES:

        - :wikipedia:`Integer-valued polynomial`

        EXAMPLES::

            sage: F = IntegerValuedPolynomialRing(QQ).S(); F
            Integer-Valued Polynomial Ring over Rational Field
            in the shifted basis

            sage: F.gen()
            S[1]

            sage: S = IntegerValuedPolynomialRing(ZZ).S(); S
            Integer-Valued Polynomial Ring over Integer Ring
            in the shifted basis
            sage: S.base_ring()
            Integer Ring

            sage: G = IntegerValuedPolynomialRing(S).S(); G
            Integer-Valued Polynomial Ring over Integer-Valued Polynomial
            Ring over Integer Ring in the shifted basis in the shifted basis
            sage: G.base_ring()
            Integer-Valued Polynomial Ring over Integer Ring
            in the shifted basis

        Integer-valued polynomial rings commute with their base ring::

            sage: K = IntegerValuedPolynomialRing(QQ).S()
            sage: a = K.gen()
            sage: K.is_commutative()
            True
            sage: L = IntegerValuedPolynomialRing(K).S()
            sage: c = L.gen()
            sage: L.is_commutative()
            True
            sage: s = a * c^3; s
            S[1]*S[1] + (-6*S[1])*S[2] + 6*S[1]*S[3]
            sage: parent(s)
            Integer-Valued Polynomial Ring over Integer-Valued Polynomial
            Ring over Rational Field in the shifted basis in the shifted basis

        Integer-valued polynomial rings are commutative::

            sage: c^3 * a == c * a * c * c
            True

        We can also manipulate elements in the basis and
        coerce elements from our base field::

            sage: F = IntegerValuedPolynomialRing(QQ).S()
            sage: S = F.basis()
            sage: S[2] * S[3]
            3*S[3] - 12*S[4] + 10*S[5]
            sage: 1 - S[2] * S[2] / 2
            S[0] - 1/2*S[2] + 3*S[3] - 3*S[4]
        """
        def __init__(self, A):
            r"""
            Initialize ``self``.

            EXAMPLES::

                sage: F = IntegerValuedPolynomialRing(QQ).S(); F
                Integer-Valued Polynomial Ring over Rational Field
                in the shifted basis
                sage: TestSuite(F).run()
            """
            CombinatorialFreeModule.__init__(self, A.base_ring(),
                                             A.indices(),
                                             category=A.Bases(),
                                             prefix="S",
                                             latex_prefix=r"\mathbb{S}")

        def _realization_name(self) -> str:
            r"""
            TESTS::

                sage: F = IntegerValuedPolynomialRing(QQ).S()
                sage: F._realization_name()
                'shifted'
            """
            return "shifted"

        def product_on_basis(self, n1, n2):
            r"""
            Return the product of basis elements ``n1`` and ``n2``.

            INPUT:

            - ``n1``, ``n2`` -- integers

            EXAMPLES::

                sage: A = IntegerValuedPolynomialRing(QQ).S()
                sage: A.product_on_basis(0, 1)
                S[1]
                sage: A.product_on_basis(1, 2)
                -2*S[2] + 3*S[3]
            """
            i = ZZ(n1)
            j = ZZ(n2)
            if j < i:
                j, i = i, j

            R = self.base_ring()
            return self._from_dict({i + j - k: R((-1)**k * i.binomial(k) * (i + j - k).binomial(i))
                                    for k in range(i + 1)})

        def _from_binomial_basis(self, i):
            """
            Convert from the ``binomial(x,k)`` basis.

            INPUT:

            - ``i`` -- an integer

            EXAMPLES::

                sage: S = IntegerValuedPolynomialRing(ZZ).S()
                sage: B = IntegerValuedPolynomialRing(ZZ).B()
                sage: b = B.basis()
                sage: S(b[3]+1)  # indirect doctest
                3*S[1] - 3*S[2] + S[3]
                sage: B(_)
                B[0] + B[3]
            """
            i = ZZ(i)
            R = self.base_ring()
            return self._from_dict({k: R((-1)**(i - k) * i.binomial(k))
                                    for k in range(i + 1)})

        def from_polynomial(self, p):
            """
            Convert a polynomial into the ring of integer-valued polynomials.

            This raises a ``ValueError`` if this is not possible.

            INPUT:

            - ``p`` -- a polynomial in one variable

            EXAMPLES::

                sage: A = IntegerValuedPolynomialRing(ZZ).S()
                sage: S = A.basis()
                sage: S[5].polynomial()
                1/120*x^5 + 1/8*x^4 + 17/24*x^3 + 15/8*x^2 + 137/60*x + 1
                sage: A.from_polynomial(_)
                S[5]
                sage: x = polygen(QQ, 'x')
                sage: A.from_polynomial(x)
                -S[0] + S[1]
            """
            B = self.basis()
            x = p.parent().gen()
            remain = p
            result = self.zero()
            while remain:
                N = remain.degree()
                top_coeff = remain.leading_coefficient() * factorial(N)
                try:
                    top_coeff = self.base_ring()(top_coeff)
                except TypeError as exc:
                    msg = 'not a polynomial with integer'
                    msg += f' values: {top_coeff}'
                    raise ValueError(msg) from exc
                remain += -top_coeff * binomial(N + x, N)
                result += top_coeff * B[N]
            return result

        def from_h_vector(self, h):
            """
            Convert from some `h`-vector.

            INPUT:

            - ``h`` -- a tuple or vector

            EXAMPLES::

                sage: A = IntegerValuedPolynomialRing(ZZ).S()
                sage: S = A.basis()
                sage: ex = S[2]+S[4]
                sage: A.from_h_vector(ex.h_vector())
                S[2] + S[4]
            """
            d = len(h) - 1
            m = matrix(QQ, d + 1, d + 1,
                       lambda j, i: (-1)**(d - j) * binomial(d - i, d - j))
            v = vector(QQ, [h[i] for i in range(d + 1)])
            return self._from_dict({i: Integer(c)
                                    for i, c in enumerate(m * v)})

        def _element_constructor_(self, x):
            r"""
            Convert ``x`` into ``self``.

            INPUT:

            - ``x`` -- an integer or something convertible

            EXAMPLES::

                sage: R = IntegerValuedPolynomialRing(QQ).S()
                sage: x = R.gen()
                sage: R(3)
                3*S[0]
                sage: R(x)
                S[1]
            """
            if x in NonNegativeIntegers():
                W = self.basis().keys()
                return self.monomial(W(x))

            P = x.parent()
            if isinstance(P, IntegerValuedPolynomialRing.Shifted):
                if P is self:
                    return x
                if P is not self.base_ring():
                    return self.element_class(self, x.monomial_coefficients())

            # ok, not a integer-valued polynomial ring element
            R = self.base_ring()
            # coercion via base ring
            x = R(x)
            if x == 0:
                return self.element_class(self, {})
            return self.from_base_ring_from_one_basis(x)

        def _coerce_map_from_(self, R):
            r"""
            Return ``True`` if there is a coercion from ``R`` into ``self``
            and ``False`` otherwise.

            INPUT:

            - ``R`` -- a commutative ring

            The things that coerce into ``self`` are

            - Integer-Valued Polynomial Rings over a base
              with a coercion map into ``self.base_ring()``.

            - Anything with a coercion into ``self.base_ring()``.

            EXAMPLES::

                sage: F = IntegerValuedPolynomialRing(GF(7)).S(); F
                Integer-Valued Polynomial Ring over Finite Field of size 7
                in the shifted basis

            Elements of the integer-valued polynomial ring canonically
            coerce in::

                sage: x = F.gen()
                sage: F.coerce(x*x) # indirect doctest
                6*S[1] + 2*S[2]

            Elements of the integers coerce in, since there is a coerce map
            from `\ZZ` to GF(7)::

                sage: F.coerce(1)       # indirect doctest
                S[0]

            There is no coerce map from `\QQ` to `\GF{7}`::

                sage: F.coerce(2/3)  # indirect doctest
                Traceback (most recent call last):
                ...
                TypeError: no canonical coercion from Rational Field to
                Integer-Valued Polynomial Ring over Finite Field of size 7
                in the shifted basis

            Elements of the base ring coerce in::

                sage: F.coerce(GF(7)(5))
                5*S[0]

            The integer-valued polynomial ring over `\ZZ` on `x` coerces in,
            since `\ZZ` coerces to `\GF{7}`::

                sage: G = IntegerValuedPolynomialRing(ZZ).S()
                sage: Gx = G.gen()
                sage: z = F.coerce(Gx**2); z
                -S[1] + 2*S[2]
                sage: z.parent() is F
                True

            However, `\GF{7}` does not coerce to `\ZZ`, so the shuffle
            algebra over `\GF{7}` does not coerce to the one over `\ZZ`::

                sage: G.coerce(x^3+x)
                Traceback (most recent call last):
                ...
                TypeError: no canonical coercion from Integer-Valued Polynomial
                Ring over Finite Field of size 7  in the shifted basis
                to Integer-Valued Polynomial
                Ring over Integer Ring in the shifted basis

            TESTS::

                sage: F = IntegerValuedPolynomialRing(ZZ).S()
                sage: G = IntegerValuedPolynomialRing(QQ).S()
                sage: H = IntegerValuedPolynomialRing(ZZ).S()
                sage: F._coerce_map_from_(G)
                False
                sage: G._coerce_map_from_(F)
                True
                sage: F._coerce_map_from_(H)
                True
                sage: F._coerce_map_from_(QQ)
                False
                sage: G._coerce_map_from_(QQ)
                True
                sage: F.has_coerce_map_from(PolynomialRing(ZZ,'x'))
                False
            """
            # integer-valued polynomial rings over any base
            # that coerces in:
            if isinstance(R, IntegerValuedPolynomialRing.Shifted):
                return self.base_ring().has_coerce_map_from(R.base_ring())
            return self.base_ring().has_coerce_map_from(R)

        class Element(CombinatorialFreeModule.Element):

            def umbra(self):
                """
                Return the Bernoulli umbra.

                This is the derivative at `-1` of the shift by one.

                EXAMPLES::

                    sage: F = IntegerValuedPolynomialRing(ZZ).S()
                    sage: B = F.gen()
                    sage: (B+1).umbra()
                    3/2

                TESTS::

                    sage: [(B**n).umbra() for n in range(1, 11)]
                    [1/2, 1/6, 0, -1/30, 0, 1/42, 0, -1/30, 0, 5/66]
                """
                return self.shift().derivative_at_minus_one()

            def delta(self):
                r"""
                Return the image by the difference operator `\Delta`.

                The operator `\Delta` is defined on polynomials by

                .. MATH::

                    f \mapsto f(x+1)-f(x).

                EXAMPLES::

                    sage: F = IntegerValuedPolynomialRing(ZZ).S()
                    sage: S = F.basis()
                    sage: S[5].delta()
                    S[0] + S[1] + S[2] + S[3] + S[4]
                """
                return self.variable_shift() - self

            def variable_shift(self, k=1):
                r"""
                Return the image by the shift of variables.

                On polynomials, the action is the shift
                on variables `x \mapsto x + 1`.

                INPUT:

                - `k` -- integer (default: 1)

                EXAMPLES::

                    sage: A = IntegerValuedPolynomialRing(ZZ).S()
                    sage: S = A.basis()
                    sage: S[5].variable_shift()
                    S[0] + S[1] + S[2] + S[3] + S[4] + S[5]
                """
                if k == 0:
                    return self

                A = self.parent()
                B = A.basis()
                resu = A.linear_combination((B[j], c) for i, c in self
                                            for j in range(i + 1))
                if k == 1:
                    return resu
                return resu.variable_shift(k - 1)

            def variable_unshift(self, k=1):
                r"""
                Return the image by the unshift of variables.

                On polynomials, the action is the shift
                on variables `x \mapsto x - k`.

                INPUT:

                - `k` -- integer (default: 1)

                EXAMPLES::

                    sage: A = IntegerValuedPolynomialRing(ZZ).S()
                    sage: S = A.basis()
                    sage: S[5].variable_unshift()
                    -S[4] + S[5]
                """
                if k == 0:
                    return self

                A = self.parent()
                resu = self - A._from_dict({i - 1: c for i, c in self if i})
                if k == 1:
                    return resu
                return resu.variable_unshift(k - 1)

            def derivative_at_minus_one(self):
                """
                Return the derivative at `-1`.

                This is sometimes useful when `-1` is a root.

                EXAMPLES::

                    sage: F = IntegerValuedPolynomialRing(ZZ).S()
                    sage: B = F.gen()
                    sage: (B+1).derivative_at_minus_one()
                    1
                """
                return QQ.sum(c / QQ(i) for i, c in self if i)

            special_value = derivative_at_minus_one

            def polynomial(self):
                """
                Convert to a standard polynomial in `x`.

                EXAMPLES::

                    sage: F = IntegerValuedPolynomialRing(ZZ).S()
                    sage: B = F.gen()
                    sage: (B+1).polynomial()
                    x + 2

                TESTS::

                    sage: F.zero().polynomial().parent()
                    Univariate Polynomial Ring in x over Rational Field
                """
                x = polygen(QQ, 'x')
                R = x.parent()
                return R.sum(c * binomial(x + i, i) for i, c in self)

            def h_vector(self):
                """
                Return the numerator of the generating series of values.

                If ``self`` is an Ehrhart polynomial, this is the `h`-vector.

                .. SEEALSO:: :meth:`h_polynomial`

                EXAMPLES::

                    sage: x = polygen(QQ,'x')
                    sage: A = IntegerValuedPolynomialRing(ZZ).S()
                    sage: ex = A.from_polynomial((1+x)**3)
                    sage: ex.h_vector()
                    (0, 1, 4, 1)
                """
                d = max(self.support(), default=-1)
                m = matrix(QQ, d + 1, d + 1,
                           lambda j, i: (-1)**(d - j) * (d - i).binomial(d - j))
                v = vector(QQ, [self.coefficient(i) for i in range(d + 1)])
                return m * v

            def h_polynomial(self):
                """
                Return the `h`-vector as a polynomial.

                .. SEEALSO:: :meth:`h_vector`

                EXAMPLES::

                    sage: x = polygen(QQ,'x')
                    sage: A = IntegerValuedPolynomialRing(ZZ).S()
                    sage: ex = A.from_polynomial((1+x)**3)
                    sage: ex.h_polynomial()
                    z^3 + 4*z^2 + z
                """
                anneau = PolynomialRing(self.parent().base_ring(), 'z')
                return anneau(list(self.h_vector()))

            def sum(self):
                """
                Return the sum of coefficients.

                This is related to the evaluation at 0.

                EXAMPLES::

                    sage: F = IntegerValuedPolynomialRing(ZZ).S()
                    sage: B = F.basis()
                    sage: (B[2]*B[4]).sum()
                    1
                """
                return sum(c for _, c in self)

    S = Shifted

    # =====     Another basis for the same algebra     =====

    class Binomial(CombinatorialFreeModule, BindableClass):
        r"""
        The integer-valued polynomial ring in the binomial basis.

        The basis used here is given by `B[i] = \binom{n}{i}` for `i \in \NN`.

        There is a conversion formula between the two bases

        .. MATH::

            \binom{x+i}{i} = \sum_{k=0}^{i} \binom{i}{k} \binom{x}{k}.

        Assuming `n_1 \leq n_2`, the product of two monomials `B[n_1] \cdot B[n_2]`
        is given by the sum

        .. MATH::

            \sum_{k=0}^{n_1} \binom{n_1}{k}\binom{n_1+n_2-k}{n_1} B[n_1 + n_2 - k].

        The product of two monomials is therefore a positive linear combination
        of monomials.

        REFERENCES:

        - :wikipedia:`Integer-valued polynomial`

        INPUT:

        - ``R`` -- ring

        EXAMPLES::

            sage: F = IntegerValuedPolynomialRing(QQ).B(); F
            Integer-Valued Polynomial Ring over Rational Field
            in the binomial basis

            sage: F.gen()
            B[1]

            sage: S = IntegerValuedPolynomialRing(ZZ).B(); S
            Integer-Valued Polynomial Ring over Integer Ring
            in the binomial basis
            sage: S.base_ring()
            Integer Ring

            sage: G = IntegerValuedPolynomialRing(S).B(); G
            Integer-Valued Polynomial Ring over Integer-Valued Polynomial Ring
            over Integer Ring in the binomial basis in the binomial basis
            sage: G.base_ring()
            Integer-Valued Polynomial Ring over Integer Ring
            in the binomial basis

        Integer-valued polynomial rings commute with their base ring::

            sage: K = IntegerValuedPolynomialRing(QQ).B()
            sage: a = K.gen()
            sage: K.is_commutative()
            True
            sage: L = IntegerValuedPolynomialRing(K).B()
            sage: c = L.gen()
            sage: L.is_commutative()
            True
            sage: s = a * c^3; s
            B[1]*B[1] + 6*B[1]*B[2] + 6*B[1]*B[3]
            sage: parent(s)
            Integer-Valued Polynomial Ring over Integer-Valued Polynomial
            Ring over Rational Field in the binomial basis in the binomial basis

        Integer-valued polynomial rings are commutative::

            sage: c^3 * a == c * a * c * c
            True

        We can also manipulate elements in the basis::

            sage: F = IntegerValuedPolynomialRing(QQ).B()
            sage: B = F.basis()
            sage: B[2] * B[3]
            3*B[3] + 12*B[4] + 10*B[5]
            sage: 1 - B[2] * B[2] / 2
            B[0] - 1/2*B[2] - 3*B[3] - 3*B[4]

        and coerce elements from our base field::

            sage: F(4/3)
            4/3*B[0]
        """
        def __init__(self, A):
            r"""
            Initialize ``self``.

            EXAMPLES::

                sage: F = IntegerValuedPolynomialRing(QQ).B(); F
                Integer-Valued Polynomial Ring over Rational Field
                in the binomial basis
                sage: TestSuite(F).run()
            """
            CombinatorialFreeModule.__init__(self, A.base_ring(), A.indices(),
                                             latex_prefix="",
                                             category=A.Bases())

        def _realization_name(self) -> str:
            r"""
            TESTS::

                sage: F = IntegerValuedPolynomialRing(QQ).B()
                sage: F._realization_name()
                'binomial'
            """
            return "binomial"

        def product_on_basis(self, n1, n2):
            r"""
            Return the product of basis elements ``n1`` and ``n2``.

            INPUT:

            - ``n1``, ``n2`` -- integers

            EXAMPLES::

                sage: A = IntegerValuedPolynomialRing(QQ).B()
                sage: A.product_on_basis(0, 1)
                B[1]
                sage: A.product_on_basis(1, 2)
                2*B[2] + 3*B[3]
            """
            i = ZZ(n1)
            j = ZZ(n2)
            if j < i:
                j, i = i, j

            R = self.base_ring()
            return self._from_dict({i + j - k:
                                    R(binomial(i, k) * binomial(i + j - k, i))
                                    for k in range(i + 1)})

        def _from_shifted_basis(self, i):
            """
            Convert from the shifted binomial(x+k,k) basis.

            INPUT:

            - ``i`` -- an integer

            EXAMPLES::

                sage: S = IntegerValuedPolynomialRing(ZZ).S()
                sage: B = IntegerValuedPolynomialRing(ZZ).B()
                sage: s = S.basis()
                sage: B(s[3]+1)  # indirect doctest
                2*B[0] + 3*B[1] + 3*B[2] + B[3]
                sage: S(_)
                S[0] + S[3]
            """
            i = ZZ(i)
            R = self.base_ring()
            return self._from_dict({k: R(i.binomial(k))
                                    for k in range(i + 1)})

        def from_polynomial(self, p):
            """
            Convert a polynomial into the ring of integer-valued polynomials.

            This raises a ``ValueError`` if this is not possible.

            INPUT:

            - ``p`` -- a polynomial in one variable

            EXAMPLES::

                sage: A = IntegerValuedPolynomialRing(ZZ).B()
                sage: B = A.basis()
                sage: B[5].polynomial()
                1/120*x^5 - 1/12*x^4 + 7/24*x^3 - 5/12*x^2 + 1/5*x
                sage: A.from_polynomial(_)
                B[5]
                sage: x = polygen(QQ, 'x')
                sage: A.from_polynomial(x)
                B[1]

            TESTS::

                sage: x = polygen(QQ,'x')
                sage: A.from_polynomial(x+1/3)
                Traceback (most recent call last):
                ...
                ValueError: not a polynomial with integer values
            """
            B = self.basis()
            x = p.parent().gen()
            remain = p
            result = self.zero()
            while remain:
                N = remain.degree()
                top_coeff = remain.leading_coefficient() * factorial(N)
                try:
                    top_coeff = self.base_ring()(top_coeff)
                except TypeError as exc:
                    raise ValueError('not a polynomial with integer values') from exc
                remain += -top_coeff * binomial(x, N)
                result += top_coeff * B[N]
            return result

        def _element_constructor_(self, x):
            r"""
            Convert ``x`` into ``self``.

            EXAMPLES::

                sage: R = IntegerValuedPolynomialRing(QQ).B()
                sage: x = R.gen()
                sage: R(3)
                3*B[0]
                sage: R(x)
                B[1]
            """
            if x in NonNegativeIntegers():
                W = self.basis().keys()
                return self.monomial(W(x))

            P = x.parent()
            if isinstance(P, IntegerValuedPolynomialRing.Binomial):
                if P is self:
                    return x
                if P is not self.base_ring():
                    return self.element_class(self, x.monomial_coefficients())

            # ok, not a integer-valued polynomial ring element
            R = self.base_ring()
            # coercion via base ring
            x = R(x)
            if x == 0:
                return self.element_class(self, {})
            return self.from_base_ring_from_one_basis(x)

        def _coerce_map_from_(self, R):
            r"""
            Return ``True`` if there is a coercion from ``R`` into ``self``
            and ``False`` otherwise.

            The things that coerce into ``self`` are

            - Integer-Valued Polynomial Rings over a base
              with a coercion map into ``self.base_ring()``.

            - Anything with a coercion into ``self.base_ring()``.

            EXAMPLES::

                sage: F = IntegerValuedPolynomialRing(GF(7)).B(); F
                Integer-Valued Polynomial Ring over Finite Field of size 7
                in the binomial basis

            Elements of the integer-valued polynomial ring canonically coerce
            in::

                sage: x = F.gen()
                sage: F.coerce(x*x) # indirect doctest
                B[1] + 2*B[2]

            Elements of the integers coerce in, since there is a coerce map
            from `\ZZ` to GF(7)::

                sage: F.coerce(1)       # indirect doctest
                B[0]

            There is no coerce map from `\QQ` to `\GF{7}`::

                sage: F.coerce(2/3)  # indirect doctest
                Traceback (most recent call last):
                ...
                TypeError: no canonical coercion from Rational Field to
                Integer-Valued Polynomial Ring over Finite Field of size 7
                in the binomial basis

            Elements of the base ring coerce in::

                sage: F.coerce(GF(7)(5))
                5*B[0]

            The integer-valued polynomial ring over `\ZZ` on `x` coerces in,
            since `\ZZ` coerces to `\GF{7}`::

                sage: G = IntegerValuedPolynomialRing(ZZ).B()
                sage: Gx = G.gen()
                sage: z = F.coerce(Gx**2); z
                B[1] + 2*B[2]
                sage: z.parent() is F
                True

            However, `\GF{7}` does not coerce to `\ZZ`, so the shuffle
            algebra over `\GF{7}` does not coerce to the one over `\ZZ`::

                sage: G.coerce(x^3+x)
                Traceback (most recent call last):
                ...
                TypeError: no canonical coercion from Integer-Valued Polynomial
                Ring over Finite Field of size 7 in the binomial basis to
                Integer-Valued Polynomial Ring over Integer Ring
                in the binomial basis

            TESTS::

                sage: F = IntegerValuedPolynomialRing(ZZ).B()
                sage: G = IntegerValuedPolynomialRing(QQ).B()
                sage: H = IntegerValuedPolynomialRing(ZZ).B()
                sage: F._coerce_map_from_(G)
                False
                sage: G._coerce_map_from_(F)
                True
                sage: F._coerce_map_from_(H)
                True
                sage: F._coerce_map_from_(QQ)
                False
                sage: G._coerce_map_from_(QQ)
                True
                sage: F.has_coerce_map_from(PolynomialRing(ZZ,'x'))
                False
            """
            # integer-valued polynomial rings over any base
            # that coerces in:
            if isinstance(R, IntegerValuedPolynomialRing.Binomial):
                return self.base_ring().has_coerce_map_from(R.base_ring())
            return self.base_ring().has_coerce_map_from(R)

        class Element(CombinatorialFreeModule.Element):

            def polynomial(self):
                """
                Convert to a standard polynomial in `x`.

                EXAMPLES::

                    sage: F = IntegerValuedPolynomialRing(ZZ).B()
                    sage: B = F.gen()
                    sage: (B+1).polynomial()
                    x + 1

                TESTS::

                    sage: F.zero().polynomial().parent()
                    Univariate Polynomial Ring in x over Rational Field
                """
                x = polygen(QQ, 'x')
                R = x.parent()
                return R.sum(c * binomial(x, i) for i, c in self)

    B = Binomial
