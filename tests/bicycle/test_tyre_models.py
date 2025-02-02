from __future__ import annotations

import pytest
from brim.bicycle.grounds import FlatGround, GroundBase
from brim.bicycle.tyre_models import NonHolonomicTyre, TyreBase
from brim.bicycle.wheels import KnifeEdgeWheel, ToroidalWheel, WheelBase
from brim.core import ConnectionRequirement, ModelBase, ModelRequirement
from sympy import cos, sin
from sympy.physics.mechanics import ReferenceFrame, cross, dynamicsymbols
from sympy.physics.mechanics._system import System


class MyTyre(TyreBase):
    pass


class TestComputeContactPoint:
    @pytest.fixture()
    def _setup_flat_ground(self):
        self.ground = FlatGround("ground")
        self.ground.define_objects()
        self.ground.define_kinematics()
        self.q = dynamicsymbols("q1:4")
        self.int_frame = ReferenceFrame("int_frame")
        self.int_frame.orient_body_fixed(self.ground.frame, (*self.q[:2], 0), "zxy")
        self.tyre = MyTyre("tyre")
        self.tyre.ground = self.ground
        self.tyre.define_objects()

    def test_knife_edge_wheel_on_flat_ground(self, _setup_flat_ground):
        wheel = KnifeEdgeWheel("wheel")
        wheel.define_objects()
        wheel.define_kinematics()
        self.tyre.wheel = wheel
        wheel.frame.orient_axis(self.int_frame, self.q[2], self.int_frame.y)
        self.tyre._set_pos_contact_point()
        assert (self.tyre.contact_point.pos_from(wheel.center) -
                wheel.symbols["r"] * self.int_frame.z).express(wheel.frame).simplify(
        ).xreplace({self.q[1]: 0.123, self.q[2]: 1.234}) == 0
        # sqrt(cos(q2)**2) is not simplified

    def test_toroidal_wheel_on_flat_ground(self, _setup_flat_ground) -> None:
        wheel = ToroidalWheel("wheel")
        wheel.define_objects()
        wheel.define_kinematics()
        self.tyre.wheel = wheel
        wheel.frame.orient_axis(self.int_frame, self.q[2], self.int_frame.y)
        self.tyre._set_pos_contact_point()
        assert (self.tyre.contact_point.pos_from(wheel.center) -
                wheel.symbols["r"] * self.int_frame.z + wheel.symbols["tr"] *
                self.ground.get_normal(self.tyre.contact_point)).express(
            wheel.frame).simplify().xreplace({self.q[1]: 0.123, self.q[2]: 1.234}) == 0
        # sqrt(cos(q2)**2) is not simplified

    def test_not_implemented_combinations(self) -> None:
        class NewGround(GroundBase):
            def get_normal(self, position):
                return -self.body.z

            def get_tangent_vectors(self, position):
                return (self.frame.x, self.frame.y)

            def set_point_pos(self, point, position) -> None:
                point.set_pos(self.origin, position[0] * self.frame.x +
                              position[1] * self.frame.y)

        class NewWheel(WheelBase):
            @property
            def center(self):
                return self.body.masscenter

            def rotation_axis(self):
                return self.frame.y

        for wheel_cls, ground_cls in [(KnifeEdgeWheel, NewGround),
                                      (NewWheel, FlatGround),
                                      (NewWheel, NewGround)]:
            tyre = MyTyre("tyre")
            tyre.ground = ground_cls("ground")
            tyre.wheel = wheel_cls("wheel")
            tyre.ground.define_objects()
            tyre.wheel.define_objects()
            tyre.define_objects()
            tyre.ground.define_kinematics()
            tyre.wheel.define_kinematics()
            with pytest.raises(NotImplementedError):
                tyre._set_pos_contact_point()

    def test_upward_radial_axis(self, _setup_flat_ground):
        wheel = KnifeEdgeWheel("wheel")
        wheel.define_objects()
        wheel.define_kinematics()
        self.tyre.wheel = wheel
        wheel.frame.orient_axis(self.int_frame, self.q[2], self.int_frame.y)
        self.tyre.upward_radial_axis = -self.int_frame.z
        self.tyre._set_pos_contact_point()
        assert (self.tyre.contact_point.pos_from(wheel.center) -
                wheel.symbols["r"] * self.int_frame.z).simplify() == 0

    def test_upward_radial_axis_invalid(self, _setup_flat_ground):
        self.tyre.wheel = KnifeEdgeWheel("wheel")
        self.tyre.wheel.define_objects()
        self.tyre.wheel.define_kinematics()
        self.tyre.wheel.frame.orient_axis(self.int_frame, self.q[2], self.int_frame.y)
        normal = self.ground.get_normal(self.tyre.contact_point)
        with pytest.raises(TypeError):  # no vector
            self.tyre.upward_radial_axis = 5
        with pytest.raises(ValueError):  # not normalize
            self.tyre.upward_radial_axis = 2 * self.int_frame.z
        with pytest.raises(ValueError):  # not radial
            self.tyre.upward_radial_axis = normal
        with pytest.raises(ValueError):  # not correct with respect to normal
            self.tyre.upward_radial_axis = cross(
                self.tyre.wheel.rotation_axis, normal).normalize()


class TestNonHolonomicTyreModel:
    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        class Model(ModelBase):
            required_models: tuple[ModelRequirement, ...] = (
                ModelRequirement("ground", FlatGround, "Submodel of the ground."),
                ModelRequirement("wheel", KnifeEdgeWheel, "Submodel of the wheel."),
            )
            required_connections: tuple[ConnectionRequirement, ...] = (
                ConnectionRequirement("tyre_model", NonHolonomicTyre,
                                      "Tyre model for the wheel."),
            )
            ground: FlatGround
            wheel: KnifeEdgeWheel
            tyre_model: NonHolonomicTyre

            def define_connections(self) -> None:
                super().define_connections()
                self.tyre_model.ground = self.ground
                self.tyre_model.wheel = self.wheel

            def define_objects(self) -> None:
                super().define_objects()
                self.tyre_model.define_objects()

            def define_kinematics(self) -> None:
                super().define_kinematics()
                self.tyre_model.define_kinematics()

            def define_loads(self) -> None:
                super().define_loads()
                self.tyre_model.define_loads()

            def define_constraints(self) -> None:
                super().define_constraints()
                self.tyre_model.define_constraints()

        self.model = Model("model")
        self.model.ground = FlatGround("ground")
        self.model.wheel = KnifeEdgeWheel("wheel")
        self.model.tyre_model = NonHolonomicTyre("tyre_model")

    def test_default(self) -> None:
        self.model.define_connections()
        self.model.define_objects()
        assert self.model.tyre_model.name == "tyre_model"
        assert isinstance(self.model.tyre_model.system, System)

    @pytest.mark.parametrize("on_ground", [True, False])
    def test_compute_on_ground(self, on_ground: bool) -> None:
        self.model.define_connections()
        self.model.define_objects()
        self.model.tyre_model.on_ground = on_ground
        ground, wheel, tyre_model = (
            self.model.ground, self.model.wheel, self.model.tyre_model)
        t = dynamicsymbols._t
        q1, q2, x, y, z = dynamicsymbols("q1 q2 x y z")
        wheel.frame.orient_body_fixed(ground.frame, (q1, q2, 0), "zyx")
        ground.set_point_pos(tyre_model.contact_point, (x, y))
        if not on_ground:
            tyre_model.contact_point.set_pos(
                ground.origin, tyre_model.contact_point.pos_from(
                    ground.origin) + z * ground.get_normal(tyre_model.contact_point))
        self.model.define_kinematics()
        self.model.define_loads()
        self.model.define_constraints()
        fnh = [
            wheel.radius * cos(q1) * q2.diff(t) + x.diff(t),
            wheel.radius * sin(q1) * q2.diff(t) + y.diff(t),
        ]
        assert len(tyre_model.system.holonomic_constraints) == int(not on_ground)
        assert len(tyre_model.system.nonholonomic_constraints) == 2
        if not on_ground:
            assert (tyre_model.system.holonomic_constraints[0] - z
                    ).simplify() == 0
        for fnhi in tyre_model.system.nonholonomic_constraints:
            assert (fnhi - fnh[0]).simplify() == 0 or (fnhi - fnh[1]).simplify() == 0
