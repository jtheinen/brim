from typing import TYPE_CHECKING

import pytest
from brim.bicycle import FlatGround, KnifeEdgeWheel, NonHolonomicTyre
from brim.other.rolling_disc import RollingDisc, rolling_disc_manual
from sympy import Symbol, lambdify
from sympy.physics.mechanics import dynamicsymbols

if TYPE_CHECKING:
    pass


class TestRollingDisc:
    @staticmethod
    def _arbitrary_values() -> dict[str, float]:
        vals = {
            "m": 1.23, "r": 0.45, "g": 9.81, "q1": 0.1, "q2": 0.3, "q3": 0.8,
            "q4": -0.4, "q5": 2.5, "u1": -0.3135180192062244,
            "u2": -0.3228102409047853, "u3": 0.4, "u4": 0.9, "u5": 1.0}
        vals["ixx"] = vals["izz"] = vals["m"] * vals["r"] ** 2 / 4
        vals["iyy"] = vals["m"] * vals["r"] ** 2 / 2
        return vals

    @pytest.fixture()
    def _rolling_disc_brim(self) -> None:
        self.rolling_disc = RollingDisc("rolling_disc")
        self.rolling_disc.disc = KnifeEdgeWheel("disc")
        self.rolling_disc.tyre = NonHolonomicTyre("tyre")
        self.rolling_disc.ground = FlatGround("ground")
        self.rolling_disc.define_connections()
        self.rolling_disc.define_objects()
        self.rolling_disc.define_kinematics()
        self.rolling_disc.define_loads()
        self.rolling_disc.define_constraints()
        self.system = self.rolling_disc.to_system()
        str_vals = self._arbitrary_values()
        inertia = self.rolling_disc.disc.body.central_inertia.to_matrix(
            self.rolling_disc.disc.frame)
        self.val_dict = {
            self.rolling_disc.disc.body.mass: str_vals["m"],
            inertia[0, 0]: str_vals["ixx"],
            inertia[1, 1]: str_vals["iyy"],
            self.rolling_disc.disc.radius: str_vals["r"],
            Symbol("g"): str_vals["g"],
            **{qi: str_vals[f"q{i}"] for i, qi in enumerate(self.rolling_disc.q, 1)},
            **{ui: str_vals[f"u{i}"] for i, ui in enumerate(self.rolling_disc.u, 1)}
        }
        self.system.u_ind = self.rolling_disc.u[2:]
        self.system.u_dep = self.rolling_disc.u[:2]
        self._set_values()

    @pytest.fixture()
    def _rolling_disc_manual(self) -> None:
        self.system = rolling_disc_manual()
        str_vals = self._arbitrary_values()
        self.val_dict = {
            **{Symbol(name): str_vals[name] for name in ("m", "r", "g", "ixx", "iyy")},
            **{dynamicsymbols(name): str_vals[name] for name in (
                "q1", "q2", "q3", "q4", "q5", "u1", "u2", "u3", "u4", "u5")}
        }
        self._set_values()

    def _set_values(self) -> None:
        self.p = tuple(
            pi for pi in self.val_dict if isinstance(pi, Symbol))
        self.p_vals = tuple(self.val_dict[pi] for pi in self.p)
        self.q0 = tuple(self.val_dict[qi] for qi in self.system.q)
        self.u0 = tuple(self.val_dict[ui] for ui in self.system.u)

    def _plot_rolling_disc_manual(self, _rolling_disc_manual) -> None:
        """Test that is not actually ran, but is useful for debugging."""
        # These are not official dependencies
        import matplotlib.pyplot as plt
        from symmeplot import SymMePlotter
        fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
        plotter = SymMePlotter(
            ax, self.system.frame, self.system.origin)
        disc = self.system.get_body("disc")
        disc_plt = plotter.add_body(disc)
        disc_plt.attach_circle(disc.masscenter, Symbol("r"), disc.y,
                               facecolor="none", edgecolor="k")
        plotter.lambdify_system((self.system.q, self.system.u, self.p))
        plotter.evaluate_system(self.q0, self.u0, self.p_vals)
        plotter.plot()
        ax.invert_zaxis()
        ax.invert_yaxis()
        plt.show()

    def _plot_rolling_disc_brim(self, _rolling_disc_brim) -> None:
        """Test that is not actually ran, but is useful for debugging."""
        # These are not official dependencies
        import matplotlib.pyplot as plt
        from brim.utilities.plotting import Plotter
        fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
        plotter = Plotter(ax, self.rolling_disc)
        plotter.lambdify_system((self.system.q, self.system.u, self.p))
        plotter.evaluate_system(self.q0, self.u0, self.p_vals)
        plotter.plot()
        ax.invert_zaxis()
        ax.invert_yaxis()
        plt.show()

    @pytest.mark.parametrize("method", ("_rolling_disc_manual", "_rolling_disc_brim"))
    def test_rolling_disc_nonholonomic(self, method, request) -> None:
        request.getfixturevalue(method)
        self.system.form_eoms()
        fnh = self.system.nonholonomic_constraints.xreplace(
            self.system.eom_method.kindiffdict())[:]
        eval_fnh = lambdify((self.system.q, self.system.u, self.p), fnh, cse=True)
        assert all(abs(val) < 1E-8 for val in eval_fnh(self.q0, self.u0, self.p_vals))

    def test_rolling_disc_description(self, _rolling_disc_brim) -> None:
        for qi in self.rolling_disc.q:
            assert self.rolling_disc.descriptions[qi]
        for ui in self.rolling_disc.u:
            assert self.rolling_disc.descriptions[ui]
