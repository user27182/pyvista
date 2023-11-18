"""Axes actor module."""
from abc import ABC, abstractmethod
from collections import namedtuple
from functools import wraps
from typing import Any, Sequence, Tuple, Union
import warnings

import numpy as np

import pyvista
from pyvista.core._typing_core import BoundsLike, Vector
from pyvista.core.errors import PyVistaDeprecationWarning
from pyvista.core.utilities.arrays import array_from_vtkmatrix, vtkmatrix_from_array
from pyvista.core.utilities.misc import assert_empty_kwargs
from pyvista.plotting import _vtk
from pyvista.plotting._property import Property, _check_range
from pyvista.plotting.actor_properties import ActorProperties
from pyvista.plotting.colors import Color, ColorLike
from pyvista.plotting.prop3d import Prop3D

AxesTuple = namedtuple('AxesTuple', ['x_shaft', 'y_shaft', 'z_shaft', 'x_tip', 'y_tip', 'z_tip'])
PartTuple = namedtuple('PartTuple', ['shaft', 'tip'])
Tuple3D = namedtuple('Tuple3D', ['x', 'y', 'z'])


def _as_nested(obj: Sequence[Any]) -> Tuple3D:
    return Tuple3D(
        x=PartTuple(shaft=obj[0], tip=obj[3]),
        y=PartTuple(shaft=obj[1], tip=obj[4]),
        z=PartTuple(shaft=obj[2], tip=obj[5]),
    )


class _AxesProp(ABC, _vtk.vtkProp):
    """Abstract class for axes-like scene props.

    This class defines a common interface for manipulating the
    geometry and properties of six Prop3D Actors representing
    the axes (three for the shafts, three for the tips) and three
    Caption Actors for the text labels (one for each axis).

    This class is designed to be a superclass for vtkAxesActor
    but is abstracted to interface with similar axes-like
    representations.
    """

    # Enforce mandatory named args to make base classes
    # explicitly init the specified parameters by name
    def __init__(
        self,
        *,
        x_label,
        y_label,
        z_label,
        labels,
        label_color,
        labels_off,
        label_size,
        x_color,
        y_color,
        z_color,
        # colors,
        visibility,
        symmetric_bounds,
        auto_length,
        properties,
    ):
        """Initialize AxesActorInterface.

        Initialize all concrete properties.

        Any properties which affect the geometry and/or positioning
        of actors in the scene are not initialized since these are
        abstracted, and subclasses will need to ensure all actors
        are updated accordingly.
        """
        super().__init__()

        # Init actors and props
        if properties is None:
            properties = dict()
        if isinstance(properties, dict):

            def _new_property():
                return Property(**properties)

        elif isinstance(properties, Property):

            def _new_property():
                return properties.copy()

        else:
            raise TypeError('`properties` must be a property object or a dictionary.')

        properties = [_new_property() for _ in range(6)]
        self._actors = self._init_actors(properties)
        (
            self._label_actors,
            self._label_setters,
            self._label_getters,
        ) = self._init_label_actors()
        [prop.SetShadow(False) for prop in self._label_text_properties]

        # Set misc flag params
        self.visibility = _set_default(visibility, True)
        self._symmetric_bounds = _set_default(symmetric_bounds, True)
        self._auto_length = _set_default(auto_length, True)

        # Set shaft and tip color. The setters will auto-set theme vals
        self.x_color = x_color
        self.y_color = y_color
        self.z_color = z_color

        # Set text labels
        if labels is None:
            self.x_label = _set_default(x_label, 'X')
            self.y_label = _set_default(y_label, 'Y')
            self.z_label = _set_default(z_label, 'Z')
        else:
            self.labels = labels
        self.labels_off = _set_default(labels_off, False)
        self.label_size = _set_default(label_size, (0.25, 0.1))
        self.label_color = label_color  # Setter will auto-set theme val

    def __del__(self):
        del self._actors
        del self._label_actors

    def __repr__(self):
        """Representation of the axes actor."""
        if self.user_matrix is None or np.array_equal(self.user_matrix, np.eye(4)):
            mat_info = 'Identity'
        else:
            mat_info = 'Set'

        if self.shaft_type == 'cylinder':
            shaft_param = 'Shaft radius:'
            shaft_value = self.shaft_radius
        else:
            shaft_param = 'Shaft width: '
            shaft_value = self.shaft_width

        bnds = self.bounds

        attr = [
            f"{type(self).__name__} ({hex(id(self))})",
            f"  X label:                    '{self.x_label}'",
            f"  Y label:                    '{self.y_label}'",
            f"  Z label:                    '{self.z_label}'",
            f"  Labels off:                 {self.labels_off}",
            f"  Label position:             {self.label_position}",
            f"  Shaft type:                 '{self.shaft_type}'",
            f"  {shaft_param}               {shaft_value}",
            f"  Shaft length:               {self.shaft_length}",
            f"  Tip type:                   '{self.tip_type}'",
            f"  Tip radius:                 {self.tip_radius}",
            f"  Tip length:                 {self.tip_length}",
            f"  Total length:               {self.total_length}",
            f"  Position:                   {self.position}",
            f"  Scale:                      {self.scale}",
            f"  User matrix:                {mat_info}",
            f"  Visible:                    {self.visibility}",
            f"  X Bounds                    {bnds[0]:.3E}, {bnds[1]:.3E}",
            f"  Y Bounds                    {bnds[2]:.3E}, {bnds[3]:.3E}",
            f"  Z Bounds                    {bnds[4]:.3E}, {bnds[5]:.3E}",
        ]
        return '\n'.join(attr)

    @abstractmethod
    def _init_actors(self, props: Sequence[Property]) -> AxesTuple:
        """Return initialized actors."""
        ...

    @abstractmethod
    def _init_label_actors(self) -> Tuple[Tuple3D, Tuple3D, Tuple3D]:
        """Return initialized captions."""
        ...

    def _init_geometry_params(
        self,
        label_position=None,
        shaft_type=None,
        shaft_radius=None,
        shaft_length=None,
        tip_type=None,
        tip_radius=0.4,
        tip_length=None,
        total_length=(1, 1, 1),
        position=(0, 0, 0),
        orientation=None,
        origin=None,
        scale=None,
        user_matrix=None,
    ):
        self.label_position = _set_default(label_position, 1.0)
        self.shaft_type = shaft_type
        self.shaft_radius = _set_default(shaft_radius, 0.01)
        self.tip_type = tip_type
        self.tip_radius = _set_default(tip_radius, 0.4)
        self.total_length = _set_default(total_length, 1.0)
        self.position = _set_default(position, (0.0, 0.0, 0.0))
        self.orientation = _set_default(orientation, (0.0, 0.0, 0.0))
        self.origin = _set_default(origin, (0.0, 0.0, 0.0))
        self.scale = _set_default(scale, 1.0)
        self.user_matrix = _set_default(user_matrix, np.eye(4))

        # Check auto-length
        # Disable flag temporarily and restore later
        auto_length_set = self.auto_length
        self.auto_length = False

        shaft_length_set = shaft_length is not None
        tip_length_set = tip_length is not None

        self.shaft_length = _set_default(shaft_length, 0.8)
        self.tip_length = _set_default(tip_length, 0.2)

        if auto_length_set:
            lengths_sum_to_one = all(
                map(lambda x, y: (x + y) == 1.0, self.shaft_length, self.tip_length)
            )
            if shaft_length_set and tip_length_set and not lengths_sum_to_one:
                raise ValueError(
                    "Cannot set both `shaft_length` and `tip_length` when `auto_length` is `True`.\n"
                    "Set either `shaft_length` or `tip_length`, but not both."
                )
            # Set property again, this time with auto-length enabled
            self.auto_length = True
            if shaft_length_set and not tip_length_set:
                self.shaft_length = shaft_length
            elif tip_length_set and not shaft_length_set:
                self.tip_length = tip_length
        else:
            self.auto_length = False

    @property
    def _actor_properties(self) -> AxesTuple:
        return AxesTuple(*[actor.GetProperty() for actor in self._actors])

    @property
    def _actor_properties_nested(self) -> Tuple3D:
        return _as_nested(self._actor_properties)

    @property
    def _actors_nested(self) -> Tuple3D:
        return _as_nested(self._actors)

    @property
    def _label_text_properties(self) -> Tuple3D:
        return Tuple3D(*[actor.GetCaptionTextProperty() for actor in self._label_actors])

    @property
    def symmetric_bounds(self) -> bool:  # numpydoc ignore=RT01
        """Enable or disable symmetry in the axes bounds calculation.

        Calculate the axes bounds as though the axes were symmetric,
        i.e. extended along -X, -Y, and -Z directions. Setting this
        parameter primarily affects camera positioning in a scene.

        - If ``True``, the axes :attr:`bounds` are symmetric about
          its :attr:`position`. Symmetric bounds allow for the axes to rotate
          about its origin, which is useful in cases where the actor
          is used as an orientation widget.

        - If ``False``, the axes :attr:`bounds` are calculated as-is.
          Asymmetric bounds are useful in cases where the axes are
          placed in a scene with other actors, since the symmetry
          could otherwise lead to undesirable camera positioning
          (e.g. camera may be positioned further away than necessary).

        Examples
        --------
        Get the symmetric bounds of the axes.

        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor(symmetric_bounds=True)
        >>> axes_actor.bounds
        (-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
        >>> axes_actor.center
        (0.0, 0.0, 0.0)

        Get the asymmetric bounds.

        >>> axes_actor.symmetric_bounds = False
        >>> axes_actor.bounds  # doctest:+SKIP
        (-0.08, 1.0, -0.08, 1.0, -0.08, 1.0)
        >>> axes_actor.center  # doctest:+SKIP
        (0.46, 0.46, 0.46)

        Show the difference in camera positioning with and without
        symmetric bounds. Orientation is added for visualization.

        >>> # Create actors
        >>> axes_actor_sym = pv.AxesActor(
        ...     orientation=(90, 0, 0), symmetric_bounds=True
        ... )
        >>> axes_actor_asym = pv.AxesActor(
        ...     orientation=(90, 0, 0), symmetric_bounds=False
        ... )
        >>>
        >>> # Show multi-window plot
        >>> pl = pv.Plotter(shape=(1, 2))
        >>> pl.subplot(0, 0)
        >>> _ = pl.add_text("Symmetric axes")
        >>> _ = pl.add_actor(axes_actor_sym)
        >>> pl.subplot(0, 1)
        >>> _ = pl.add_text("Asymmetric axes")
        >>> _ = pl.add_actor(axes_actor_asym)
        >>> pl.show()

        """
        return self._symmetric_bounds

    @symmetric_bounds.setter
    def symmetric_bounds(self, value: bool):  # numpydoc ignore=GL08
        self._symmetric_bounds = bool(value)

    @property
    def visibility(self) -> bool:  # numpydoc ignore=RT01
        """Enable or disable the visibility of the axes.

        Examples
        --------
        Create an AxesActor and check its visibility

        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.visibility
        True

        """
        return bool(self.GetVisibility())

    @visibility.setter
    def visibility(self, value: bool):  # numpydoc ignore=GL08
        self.SetVisibility(value)

    @property
    def total_length(self) -> Tuple[float, float, float]:  # numpydoc ignore=RT01
        """Total length of each axis (shaft plus tip).

        Values must be non-negative.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.total_length
        (1.0, 1.0, 1.0)
        >>> axes_actor.total_length = 1.2
        >>> axes_actor.total_length
        (1.2, 1.2, 1.2)
        >>> axes_actor.total_length = (1.0, 0.9, 0.5)
        >>> axes_actor.total_length
        (1.0, 0.9, 0.5)

        """
        return self._total_length

    @total_length.setter
    def total_length(self, length: Union[float, Vector]):  # numpydoc ignore=GL08
        if isinstance(length, (int, float)):
            _check_range(length, (0, float('inf')), 'total_length')
            length = (length, length, length)
        _check_range(length[0], (0, float('inf')), 'x-axis total_length')
        _check_range(length[1], (0, float('inf')), 'y-axis total_length')
        _check_range(length[2], (0, float('inf')), 'z-axis total_length')
        self._total_length = float(length[0]), float(length[1]), float(length[2])

    # @property
    # @abstractmethod
    # def _total_length(self):
    #     ...

    @property
    def shaft_length(self) -> Tuple[float, float, float]:  # numpydoc ignore=RT01
        """Normalized length of the shaft for each axis.

        Values must be in range ``[0, 1]``.

        Notes
        -----
        Setting this property will automatically change the :attr:`tip_length` to
        ``1 - shaft_length`` if :attr:`auto_shaft_type` is ``True``.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.shaft_length
        (0.8, 0.8, 0.8)
        >>> axes_actor.shaft_length = 0.7
        >>> axes_actor.shaft_length
        (0.7, 0.7, 0.7)
        >>> axes_actor.shaft_length = (1.0, 0.9, 0.5)
        >>> axes_actor.shaft_length
        (1.0, 0.9, 0.5)

        """
        return self._shaft_length

    @shaft_length.setter
    def shaft_length(self, length: Union[float, Vector]):  # numpydoc ignore=GL08
        if isinstance(length, (int, float)):
            _check_range(length, (0, 1), 'shaft_length')
            length = (length, length, length)
        _check_range(length[0], (0, 1), 'x-axis shaft_length')
        _check_range(length[1], (0, 1), 'y-axis shaft_length')
        _check_range(length[2], (0, 1), 'z-axis shaft_length')
        self._shaft_length = float(length[0]), float(length[1]), float(length[2])

        if self.auto_length:
            # Calc 1-length and round to nearest 1e-8
            def calc(x):
                return round(1.0 - x, 8)

            self._tip_length = calc(length[0]), calc(length[1]), calc(length[2])

    # @property
    # @abstractmethod
    # def _shaft_length(self):
    #     ...

    @property
    def tip_length(self) -> Tuple[float, float, float]:  # numpydoc ignore=RT01
        """Normalized length of the tip for each axis.

        Values must be in range ``[0, 1]``.

        Notes
        -----
        Setting this property will automatically change the :attr:`shaft_length` to
        ``1 - tip_length`` if :attr:`auto_shaft_type` is ``True``.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.tip_length
        (0.2, 0.2, 0.2)
        >>> axes_actor.tip_length = 0.3
        >>> axes_actor.tip_length
        (0.3, 0.3, 0.3)
        >>> axes_actor.tip_length = (0.1, 0.4, 0.2)
        >>> axes_actor.tip_length
        (0.1, 0.4, 0.2)

        """
        return self._tip_length

    @tip_length.setter
    def tip_length(self, length: Union[float, Vector]):  # numpydoc ignore=GL08
        if isinstance(length, (int, float)):
            _check_range(length, (0, 1), 'tip_length')
            length = (length, length, length)
        _check_range(length[0], (0, 1), 'x-axis tip_length')
        _check_range(length[1], (0, 1), 'y-axis tip_length')
        _check_range(length[2], (0, 1), 'z-axis tip_length')
        self._tip_length = float(length[0]), float(length[1]), float(length[2])

        if self.auto_length:
            # Calc 1-length and round to nearest 1e-8
            def calc(x):
                return round(1.0 - x, 8)

            self._shaft_length = calc(length[0]), calc(length[1]), calc(length[2])

    # @property
    # @abstractmethod
    # def _tip_length(self):
    #     ...

    @property
    def label_position(self) -> Tuple[float, float, float]:  # numpydoc ignore=RT01
        """Normalized position of the text label along each axis.

        Values must be non-negative.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.label_position
        (1.0, 1.0, 1.0)
        >>> axes_actor.label_position = 0.3
        >>> axes_actor.label_position
        (0.3, 0.3, 0.3)
        >>> axes_actor.label_position = (0.1, 0.4, 0.2)
        >>> axes_actor.label_position
        (0.1, 0.4, 0.2)

        """
        return self._label_position

    @label_position.setter
    def label_position(self, position: Union[float, Vector]):  # numpydoc ignore=GL08
        if isinstance(position, (int, float)):
            _check_range(position, (0, float('inf')), 'label_position')
            position = [position, position, position]
        _check_range(position[0], (0, float('inf')), 'x-axis label_position')
        _check_range(position[1], (0, float('inf')), 'y-axis label_position')
        _check_range(position[2], (0, float('inf')), 'z-axis label_position')
        self._label_position = float(position[0]), float(position[1]), float(position[2])

    # @property
    # @abstractmethod
    # def _label_position(self):
    #     ...

    @property
    def auto_length(self) -> bool:  # numpydoc ignore=RT01
        """Automatically set shaft length when setting tip length and vice-versa.

        If ``True``:

        - Setting :attr:`shaft_length` will also set :attr:`tip_length`
          to ``1 - shaft_length``.
        - Setting :attr:`tip_length` will also set :attr:`shaft_length`
          to ``1 - tip_length``.

        Examples
        --------
        Create an axes actor with a specific shaft length.

        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor(shaft_length=0.7, auto_length=True)
        >>> axes_actor.shaft_length
        (0.7, 0.7, 0.7)
        >>> axes_actor.tip_length
        (0.3, 0.3, 0.3)

        The tip lengths are adjusted dynamically.

        >>> axes_actor.tip_length = (0.1, 0.2, 0.4)
        >>> axes_actor.tip_length
        (0.1, 0.2, 0.4)
        >>> axes_actor.shaft_length
        (0.9, 0.8, 0.6)

        """
        return self._auto_length

    @auto_length.setter
    def auto_length(self, value: bool):  # numpydoc ignore=GL08
        self._auto_length = bool(value)

    @property
    def tip_radius(self) -> float:  # numpydoc ignore=RT01
        """Radius of the axes tips.

        Value must be non-negative.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.tip_radius
        0.4
        >>> axes_actor.tip_radius = 0.8
        >>> axes_actor.tip_radius
        0.8

        """
        return self._tip_radius

    @tip_radius.setter
    def tip_radius(self, radius: float):  # numpydoc ignore=GL08
        _check_range(radius, (0, float('inf')), 'tip_radius')
        self._tip_radius = radius

    # @property
    # @abstractmethod
    # def _tip_radius(self):
    #     ...

    @property
    def shaft_radius(self):  # numpydoc ignore=RT01
        """Cylinder radius of the axes shafts.

        Value must be non-negative.

        Notes
        -----
        Setting this property will automatically change the ``shaft_type`` to
        ``'cylinder'`` if :attr:`auto_shaft_type` is ``True``.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.shaft_radius
        0.01
        >>> axes_actor.shaft_radius = 0.03
        >>> axes_actor.shaft_radius
        0.03

        """
        return self._shaft_radius

    @shaft_radius.setter
    def shaft_radius(self, radius):  # numpydoc ignore=GL08
        _check_range(radius, (0, float('inf')), 'shaft_radius')
        self._shaft_radius = radius

    # @property
    # @abstractmethod
    # def _shaft_radius(self):
    #     ...

    @property
    def shaft_type(self) -> str:  # numpydoc ignore=RT01
        """Tip type for all axes.

        Can be a cylinder (``0`` or ``'cylinder'``) or a line (``1`` or ``'line'``).

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.shaft_type = "line"
        >>> axes_actor.shaft_type
        'line'

        """
        return self._shaft_type

    @shaft_type.setter
    def shaft_type(self, shaft_type: str):  # numpydoc ignore=GL08
        if shaft_type is None:
            shaft_type = pyvista.global_theme.axes.shaft_type
        self._shaft_type = shaft_type

    # @property
    # @abstractmethod
    # def _shaft_type(self):
    #     ...

    @property
    def tip_type(self) -> str:  # numpydoc ignore=RT01
        """Tip type for all axes.

        Can be a cone (``0`` or ``'cone'``) or a sphere (``1`` or ``'sphere'``).

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.tip_type = 'sphere'
        >>> axes_actor.tip_type
        'sphere'

        """
        return self._tip_type

    @tip_type.setter
    def tip_type(self, tip_type: str):  # numpydoc ignore=GL08
        if tip_type is None:
            tip_type = pyvista.global_theme.axes.tip_type
        self._tip_type = tip_type

    # @property
    # @abstractmethod
    # def _tip_type(self):
    #     ...

    @property
    def labels(self) -> Tuple[str, str, str]:  # numpydoc ignore=RT01
        """Axes text labels.

        This property can be used as an alternative to using :attr:`~x_label`,
        :attr:`~y_label`, and :attr:`~z_label` separately for setting or
        getting the axes text labels.

        A single string with exactly three characters can be used to set the labels
        of the x, y, and z axes (respectively) to a single character. Alternatively.
        a sequence of three strings can be used.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.labels = 'UVW'
        >>> axes_actor.labels
        ('U', 'V', 'W')
        >>> axes_actor.labels = ['X Axis', 'Y Axis', 'Z Axis']
        >>> axes_actor.labels
        ('X Axis', 'Y Axis', 'Z Axis')

        """
        return self.x_label, self.y_label, self.z_label

    @labels.setter
    def labels(self, labels: Union[str, Sequence[str]]):  # numpydoc ignore=GL08
        self.x_label = labels[0]
        self.y_label = labels[1]
        self.z_label = labels[2]
        if len(labels) > 3:
            raise ValueError('Labels sequence must have exactly 3 items.')

    @property
    def x_label(self) -> str:  # numpydoc ignore=RT01
        """Text label for the x-axis.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.x_label = 'This axis'
        >>> axes_actor.x_label
        'This axis'

        """
        return self._label_getters.x()

    @x_label.setter
    def x_label(self, label: str):  # numpydoc ignore=GL08
        self._label_setters.x(label)

    @property
    def y_label(self) -> str:  # numpydoc ignore=RT01
        """Text label for the y-axis.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.y_label = 'This axis'
        >>> axes_actor.y_label
        'This axis'

        """
        return self._label_getters.y()

    @y_label.setter
    def y_label(self, label: str):  # numpydoc ignore=GL08
        self._label_setters.y(label)

    @property
    def z_label(self) -> str:  # numpydoc ignore=RT01
        """Text label for the z-axis.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.z_label = 'This axis'
        >>> axes_actor.z_label
        'This axis'

        """
        return self._label_getters.z()

    @z_label.setter
    def z_label(self, label: str):  # numpydoc ignore=GL08
        self._label_setters.z(label)

    @property
    def x_shaft_prop(self) -> Property:  # numpydoc ignore=RT01
        """Return or set the property object of the x-axis shaft."""
        return self._actor_properties.x_shaft

    @x_shaft_prop.setter
    def x_shaft_prop(self, prop: Property):  # numpydoc ignore=RT01,GL08
        self._set_prop_obj(prop, axis=0, part=0)

    @property
    def y_shaft_prop(self) -> Property:  # numpydoc ignore=RT01
        """Return or set the property object of the y-axis shaft."""
        return self._actor_properties.y_shaft

    @y_shaft_prop.setter
    def y_shaft_prop(self, prop: Property):  # numpydoc ignore=RT01,GL08
        self._set_prop_obj(prop, axis=1, part=0)

    @property
    def z_shaft_prop(self) -> Property:  # numpydoc ignore=RT01
        """Return or set the property object of the z-axis shaft."""
        return self._actor_properties.z_shaft

    @z_shaft_prop.setter
    def z_shaft_prop(self, prop: Property):  # numpydoc ignore=RT01,GL08
        self._set_prop_obj(prop, axis=2, part=0)

    @property
    def x_tip_prop(self) -> Property:  # numpydoc ignore=RT01
        """Return or set the property object of the x-axis tip."""
        return self._actor_properties.x_tip

    @x_tip_prop.setter
    def x_tip_prop(self, prop: Property):  # numpydoc ignore=RT01,GL08
        self._set_prop_obj(prop, axis=0, part=1)

    @property
    def y_tip_prop(self) -> Property:  # numpydoc ignore=RT01
        """Return or set the property object of the y-axis tip."""
        return self._actor_properties.y_tip

    @y_tip_prop.setter
    def y_tip_prop(self, prop: Property):  # numpydoc ignore=RT01,GL08
        self._set_prop_obj(prop, axis=1, part=1)

    @property
    def z_tip_prop(self) -> Property:  # numpydoc ignore=RT01
        """Return or set the property object of the z-axis tip."""
        return self._actor_properties.z_tip

    @z_tip_prop.setter
    def z_tip_prop(self, prop: Property):  # numpydoc ignore=RT01,GL08
        self._set_prop_obj(prop, axis=2, part=1)

    def _set_prop_obj(self, prop: Property, axis: int, part: int):
        """Set actor property objects."""
        if not isinstance(prop, Property):
            raise TypeError(f'Prop must have type {Property}, got {type(prop)} instead.')
        self._actors_nested[axis][part].SetProperty(prop)

    def set_prop(self, name, value, axis='all', part='all'):
        """Set the axes shaft and tip properties.

        This is a generalized setter method which sets the value of
        a specific property for any combination of axis shaft or tip
        :class:`pyvista.Property` objects.

        Parameters
        ----------
        name : str
            Name of the property to set.

        value : Any
            Value to set the property to.

        axis : str | int, default: 'all'
            Set the property for a specific part of the axes. Specify one of:

            - ``'x'`` or ``0``: only set the property for the x-axis.
            - ``'y'`` or ``1``: only set the property for the y-axis.
            - ``'z'`` or ``2``: only set the property for the z-axis.
            - ``'all'``: set the property for all three axes.

        part : str | int, default: 'all'
            Set the property for a specific part of the axes. Specify one of:

            - ``'shaft'`` or ``0``: only set the property for the axes shafts.
            - ``'tip'`` or ``1``: only set the property for the axes tips.
            - ``'all'``: set the property for axes shafts and tips.

        Examples
        --------
        Set the ambient property for all axes shafts and tips.

        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.set_prop('ambient', 0.7)
        >>> axes_actor.get_prop('ambient')
        AxesTuple(x_shaft=0.7, y_shaft=0.7, z_shaft=0.7, x_tip=0.7, y_tip=0.7, z_tip=0.7)

        Set a property for the x-axis only. The property is set for
        both the axis shaft and tip by default.

        >>> axes_actor.set_prop('ambient', 0.3, axis='x')
        >>> axes_actor.get_prop('ambient')
        AxesTuple(x_shaft=0.3, y_shaft=0.7, z_shaft=0.7, x_tip=0.3, y_tip=0.7, z_tip=0.7)

        Set a property for the axes tips only. The property is set for
        all axes by default.

        >>> axes_actor.set_prop('ambient', 0.1, part='tip')
        >>> axes_actor.get_prop('ambient')
        AxesTuple(x_shaft=0.3, y_shaft=0.7, z_shaft=0.7, x_tip=0.1, y_tip=0.1, z_tip=0.1)

        Set a property for a single axis and specific part.

        >>> axes_actor.set_prop('ambient', 0.9, axis='z', part='shaft')
        >>> axes_actor.get_prop('ambient')
        AxesTuple(x_shaft=0.3, y_shaft=0.7, z_shaft=0.9, x_tip=0.1, y_tip=0.1, z_tip=0.1)

        The last example is equivalent to setting the property directly.

        >>> axes_actor.z_shaft_prop.ambient = 0.9
        >>> axes_actor.get_prop('ambient')
        AxesTuple(x_shaft=0.3, y_shaft=0.7, z_shaft=0.9, x_tip=0.1, y_tip=0.1, z_tip=0.1)

        """
        props_dict = self._filter_prop_objects(axis=axis, part=part)
        for prop in props_dict.values():
            setattr(prop, name, value)

    def get_prop(self, name):
        """Get the axes shaft and tip properties.

        This is a generalized getter method which returns the value of
        a specific property for all shaft and tip :class:`pyvista.Property` objects.

        Parameters
        ----------
        name : str
            Name of the property to set.

        Returns
        -------
        AxesTuple
            Named tuple with the requested property value for the axes shafts and tips.

        Examples
        --------
        Get the ambient property of the axes shafts and tips.

        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.get_prop('ambient')
        AxesTuple(x_shaft=0.0, y_shaft=0.0, z_shaft=0.0, x_tip=0.0, y_tip=0.0, z_tip=0.0)

        """
        props = [getattr(prop, name) for prop in self._actor_properties]
        return AxesTuple(*props)

    def _filter_prop_objects(self, axis: Union[str, int] = 'all', part: Union[str, int] = 'all'):
        valid_axis = [0, 1, 2, 'x', 'y', 'z', 'all']
        if axis not in valid_axis:
            raise ValueError(f"Axis must be one of {valid_axis}.")
        valid_part = [0, 1, 'shaft', 'tip', 'all']
        if part not in valid_part:
            raise ValueError(f"Part must be one of {valid_part}.")

        props = dict()
        for num, char in enumerate(['x', 'y', 'z']):
            if axis in [num, char, 'all']:
                if part in [0, 'shaft', 'all']:
                    key = char + '_shaft'
                    props[key] = getattr(self._actor_properties, key)
                if part in [1, 'tip', 'all']:
                    key = char + '_tip'
                    props[key] = getattr(self._actor_properties, key)

        return props

    def plot(self, **kwargs):
        """Plot just the axes actor.

        This may be useful when interrogating or debugging the axes.

        Parameters
        ----------
        **kwargs : dict, optional
            Optional keyword arguments passed to :func:`pyvista.Plotter.show`.

        Examples
        --------
        Create an axes actor without the :class:`pyvista.Plotter`,
        and replace its shaft and tip properties with default
        :class:`pyvista.Property` objects.

        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.x_shaft_prop = pv.Property()
        >>> axes_actor.y_shaft_prop = pv.Property()
        >>> axes_actor.z_shaft_prop = pv.Property()
        >>> axes_actor.x_tip_prop = pv.Property()
        >>> axes_actor.y_tip_prop = pv.Property()
        >>> axes_actor.z_tip_prop = pv.Property()
        >>> axes_actor.plot()

        Restore the default colors.

        >>> axes_actor.x_color = pv.global_theme.axes.x_color
        >>> axes_actor.y_color = pv.global_theme.axes.y_color
        >>> axes_actor.z_color = pv.global_theme.axes.z_color
        >>> axes_actor.plot()
        """
        pl = pyvista.Plotter()
        pl.add_actor(self)
        pl.show(**kwargs)

    @property
    def label_color(self) -> Tuple[Color, Color, Color]:  # numpydoc ignore=RT01
        """Color of the label text for all axes."""
        props = self._label_text_properties
        colors = [prop.GetColor() for prop in props]
        opacities = [prop.GetOpacity() for prop in props]
        return (
            Color(colors[0], opacity=opacities[0]),
            Color(colors[1], opacity=opacities[1]),
            Color(colors[2], opacity=opacities[2]),
        )

    @label_color.setter
    def label_color(self, color: Union[ColorLike, Sequence[ColorLike]]):  # numpydoc ignore=GL08
        if color is None:
            color = Color(color, default_color=pyvista.global_theme.font.color)
        colors = _validate_color_sequence(color, num_colors=3)
        props = self._label_text_properties

        props[0].SetColor(colors[0].float_rgb)
        props[1].SetColor(colors[1].float_rgb)
        props[2].SetColor(colors[2].float_rgb)

        props[0].SetOpacity(colors[0].float_rgba[3])
        props[1].SetOpacity(colors[1].float_rgba[3])
        props[2].SetOpacity(colors[2].float_rgba[3])

    @property
    def x_color(self) -> Tuple[Color, Color]:  # numpydoc ignore=RT01
        """Color of the x-axis shaft and tip."""
        return self._get_axis_color(axis=0)

    @x_color.setter
    def x_color(self, color: Union[ColorLike, Sequence[ColorLike]]):  # numpydoc ignore=GL08
        self._set_axis_color(axis=0, color=color)

    @property
    def y_color(self) -> Tuple[Color, Color]:  # numpydoc ignore=RT01
        """Color of the y-axis shaft and tip."""
        return self._get_axis_color(axis=1)

    @y_color.setter
    def y_color(self, color: Union[ColorLike, Sequence[ColorLike]]):  # numpydoc ignore=GL08
        self._set_axis_color(axis=1, color=color)

    @property
    def z_color(self) -> Tuple[Color, Color]:  # numpydoc ignore=RT01
        """Color of the z-axis shaft and tip."""
        return self._get_axis_color(axis=2)

    @z_color.setter
    def z_color(self, color: Union[ColorLike, Sequence[ColorLike]]):  # numpydoc ignore=GL08
        self._set_axis_color(axis=2, color=color)

    def _get_axis_color(self, axis):
        prop = self._actor_properties_nested[axis]
        shaft = Color(color=prop.shaft.color, opacity=prop.shaft.opacity)
        tip = Color(color=prop.tip.color, opacity=prop.tip.opacity)
        return PartTuple(shaft, tip)

    def _set_axis_color(self, axis, color):
        if color is None:
            if axis == 0:
                color = pyvista.global_theme.axes.x_color
            elif axis == 1:
                color = pyvista.global_theme.axes.y_color
            else:
                color = pyvista.global_theme.axes.z_color
            colors = [Color(color)] * 2
        else:
            colors = _validate_color_sequence(color, num_colors=2)

        self._actor_properties_nested[axis].shaft.color = colors[0].float_rgb
        self._actor_properties_nested[axis].shaft.opacity = colors[0].float_rgba[3]
        self._actor_properties_nested[axis].tip.color = colors[1].float_rgb
        self._actor_properties_nested[axis].tip.opacity = colors[1].float_rgba[3]

    @property
    @abstractmethod
    def labels_off(self):
        ...

    @property
    def label_size(self) -> Tuple[float, float]:  # numpydoc ignore=RT01
        """The width and height of the axes labels.

        The width and height are expressed as a fraction of the viewport.
        Values must be in range ``[0, 1]``.
        """
        # Get x label size and assume all sizes are the same
        return self._label_actors.x.GetWidth(), self._label_actors.x.GetHeight()

    @label_size.setter
    def label_size(self, size: Sequence[float]):  # numpydoc ignore=GL08
        _check_range(size[0], (0, float('inf')), 'label_size width')
        _check_range(size[1], (0, float('inf')), 'label_size height')
        for actor in self._label_actors:
            actor.SetWidth(size[0])
            actor.SetHeight(size[1])


def _validate_color_sequence(color: Union[ColorLike, Sequence[ColorLike]], num_colors):
    is_valid = False
    try:
        color = [Color(color)] * num_colors
        is_valid = True
    except ValueError:
        if isinstance(color, Sequence) and len(color) == num_colors:
            # if isinstance(color, str):
            #     # Create list of individual characters
            #     color = [c for c in color]
            try:
                color = [Color(c) for c in color]
                is_valid = True
            except ValueError:
                pass
    if not is_valid:
        raise ValueError(
            f"Invalid color(s). Input must be a single ColorLike color \n"
            f"or a sequence of {num_colors} ColorLike colors."
        )
    return color


class AxesActor(_AxesProp, Prop3D, _vtk.vtkAxesActor):
    """Create a hybrid 2D/3D actor to represent 3D axes in a scene.

    The axes colors, labels, and shaft/tip geometry can all be customized.
    The axes can also be arbitrarily positioned and oriented in a scene.

    .. versionadded:: 0.43.0

        Improved initialization

        - All ``AxesActor`` parameters can be initialized by
          the constructor.
        - Added ``properties`` keyword to initialize surface :class:`pyvista.Property`
          values (e.g. ``ambient``, ``specular``, etc.).

        Axes are orientable in space

        - Added spatial properties :attr:`position`, :attr:`orientation`
          , :attr:`scale`, :attr:`origin`, and :attr:`user_matrix`
          from :class:`pyvista.Prop3D`.
        - Added spatial methods :func:`rotate_x`, :func:`rotate_y`
          , :func:`rotate_z` from :class:`pyvista.Prop3D`.
        - Added bounds-related parameters :attr:`bounds`, :attr:`center`
          , :attr:`length`, and :attr:`symmetric_bounds`.

        New label properties

        - Added color properties :attr:`label_color`, :attr:`x_color`
          , :attr:`y_color`, and :attr:`z_color`.
        - Added :attr:`label_size` property.
        - Added :attr:`labels` property.

        Improved manipulation of shaft and tip actor properties

        - Shaft and tip actor properties now make use of
          the :class:`pyvista.Property` API.
        - Added :func:`set_prop` and :func:`get_prop`.

        API Improvements

        - Added :func:`plot` method.
        - The shaft and tip type can be set using strings.
          Previously, the use of a ``ShaftType`` or ``TipType``
          Enum was required.
        - Added :attr:`auto_shaft_type`.
        - Added :attr:`auto_length`.
        - Added :attr:`true_to_scale`.

    .. versionchanged:: 0.43.0

        New default shaft type

        - The default shaft type is changed from ``'line'``
          to ``'cylinder'``.

        Shaft and tip property abstraction

        - Shaft and tip property names are abstracted.
        - e.g. use :attr:`tip_radius` to set the radius of the
          axes tips regardless of the :attr:`tip_type` used.
          Previously, it was necessary to use ``cone_radius``
          or ``sphere_radius`` separately.
        - The use of non-abstract properties is deprecated, see
          below for details.
        - The shaft type is now modified when setting cylinder-
          or line- specific parameters. See :attr:`auto_shaft_type`
          for details.

        Theme changes

        - The axes shaft and tip type are now included be
          in :class:`pyvista.plotting.themes._AxesConfig`.
        - Axes shaft and tip properties now apply default theme
          parameters set by :class:`pyvista.Property`.

    .. deprecated:: 0.43.0

        Abstracted properties

        - ``cone_radius`` ->  use :attr:`~tip_radius` instead.
        - ``cone_resolution`` -> use :attr:`~tip_resolution` instead.
        - ``cylinder_resolution`` -> use :attr:`~shaft_resolution` instead.
        - ``cylinder_radius`` -> use :attr:`~shaft_radius` instead.
        - ``line_width`` -> use :attr:`~shaft_width` instead.
        - ``sphere_radius`` -> use :attr:`~tip_radius` instead.
        - ``sphere_resolution`` -> use :attr:`~tip_resolution` instead.

        Renamed properties

        - ``x_axis_label`` -> use :attr:`~x_label` instead.
        - ``y_axis_label`` -> use :attr:`~y_label` instead.
        - ``z_axis_label`` -> use :attr:`~z_label` instead.
        - ``x_axis_shaft_properties`` -> use :attr:`~x_shaft_prop` instead.
        - ``y_axis_shaft_properties`` -> use :attr:`~y_shaft_prop` instead.
        - ``z_axis_shaft_properties`` -> use :attr:`~z_shaft_prop` instead.
        - ``x_axis_tip_properties`` -> use :attr:`~x_tip_prop` instead.
        - ``y_axis_tip_properties`` -> use :attr:`~y_tip_prop` instead.
        - ``z_axis_tip_properties`` -> use :attr:`~z_tip_prop` instead.

    .. warning::

        Positioning and orienting the axes in space by setting ``position``,
        ``orientation``, etc. is an experimental feature. In some cases, this
        may result in the axes not being visible when plotting the axes. Call
        :func:`pyvista.Plotter.reset_camera` with :attr:`pyvista.Plotter.bounds`
        (e.g. ``pl.reset_camera(pl.bounds)``) to reset the camera if necessary.

    Parameters
    ----------
    x_label : str, default: "X"
        Text label for the x-axis.

    y_label : str, default: "Y"
        Text label for the y-axis.

    z_label : str, default: "Z"
        Text label for the z-axis.

    labels : str | Sequence[str], optional
        Alternative parameter for setting text labels. Setting this
        parameter is equivalent to setting ``x_label``, ``y_label``, and
        ``z_label`` separately. Value must be a sequence of three strings
        or a single string with three characters (one for each of the x,
        y, and z axes, respectively). If set, the specified labels will take
        precedence, i.e. the values of ``x_label``, etc. are ignored.

    label_color : ColorLike, optional
        Color of the label text for all axes.

    labels_off : bool, default: False
        Enable or disable the text labels for the axes.

    label_size : Sequence[float], default: (0.25, 0.1)
        The width and height of the axes labels expressed as a fraction
        of the viewport. Values must be in range ``[0, 1]``.

    label_position : float | Vector, default: 1
        Normalized label position along the axes shafts. If a number,
        the label position for all axes is set to this value. Values
        should be non-negative.

    x_color : ColorLike, default: :attr:`pyvista.plotting.themes._AxesConfig.x_color`
        Color of the x-axis shaft and tip.

    y_color : ColorLike, default: :attr:`pyvista.plotting.themes._AxesConfig.y_color`
        Color of the y-axis shaft and tip.

    z_color : ColorLike, default: :attr:`pyvista.plotting.themes._AxesConfig.z_color`
        Color of the z-axis shaft and tip.

    shaft_type : str | AxesActor.ShaftType, default: :attr:`pyvista.plotting.themes._AxesConfig.shaft_type`
        Shaft type of the axes, either ``'cylinder'`` or ``'line'``.

    shaft_radius : float, default: 0.01
        Cylinder radius of the axes shafts. Value must be non-negative.
        Only has an effect on the rendered axes if ``shaft_type`` is
        ``'cylinder'``.

    shaft_width : float, default: 2
        Line width of the axes shafts in screen units. Value must be
        non-negative. Only has an effect on the rendered axes if
        ``shaft_type`` is ``'line'``.

    shaft_length : float | Vector, default: 0.8
        Normalized length of the shaft for each axis. If a number, the shaft
        length for all axes is set to this value. Values should be in range
        ``[0, 1]``.

    shaft_resolution : int, default: 16
        Resolution of the axes shafts. Value must be a positive integer.
        Only has an effect if ``shaft_type`` is ``'cylinder'``.

    tip_type : str | AxesActor.TipType, default: :attr:`pyvista.plotting.themes._AxesConfig.tip_type`
        Tip type of the axes, either ``'cone'`` or ``'sphere'``.

    tip_radius : float, default: 0.4
        Radius of the axes tips. Value must be non-negative.

    tip_length : float | Vector, default: 0.2
        Normalized length of the axes tips. If a number, the shaft
        length for all axes is set to this value. Values should be in range
        ``[0, 1]``.

    tip_resolution : int , default: 16
        Resolution of the axes tips. Value must be a positive integer.

    total_length : float | Vector, default: (1, 1, 1)
        Total length of each axis (shaft plus tip). Values must be
        non-negative.

    position : Vector, default: (0, 0, 0)
        Position of the axes.

    orientation : Vector, default: (0, 0, 0)
        Orientation angles of the axes which define rotations about the
        world's x-y-z axes. The angles are specified in degrees and in
        x-y-z order. However, the actual rotations are applied in the
        following order: :func:`~rotate_y` first, then :func:`~rotate_x`
        and finally :func:`~rotate_z`.

    origin : Vector, default: (0, 0, 0)
        Origin of the axes. This is the point about which all
        rotations take place.

    scale : float | Vector, default: (1, 1, 1)
        Scaling factor for the axes.

    user_matrix : vtkMatrix3x3 | vtkMatrix4x4 | vtkTransform | np.ndarray
        Transformation to apply to the axes. Can be a vtkTransform,
        3x3 transformation matrix, or 4x4 transformation matrix.
        Defaults to the identity matrix.

    visibility : bool, default: True
        Visibility of the axes. If ``False``, the axes are not visible.

    symmetric_bounds : bool, default: True
        Calculate the axes bounds as though the axes were symmetric,
        i.e. extended along -X, -Y, and -Z directions. Setting this
        parameter primarily affects camera positioning in a scene.

        - If ``True``, the axes :attr:`bounds` are symmetric about
          its :attr:`position`. Symmetric bounds allow for the axes to rotate
          about its origin, which is useful in cases where the actor
          is used as an orientation widget.
        - If ``False``, the axes :attr:`bounds` are calculated as-is.
          Asymmetric bounds are useful in cases where the axes are
          placed in a scene with other actors, since the symmetry
          could otherwise lead to undesirable camera positioning
          (e.g. camera is positioned further away than necessary).

    auto_shaft_type : bool, default: True
        Automatically adjust related properties when setting
        certain properties. If ``True``:

        - Setting :attr:`shaft_width` will also set :attr:`shaft_type`
          to ``'line'``.

    auto_length : bool, default: True
        Automatically set shaft length when setting tip length and vice-versa.
        If ``True``:

        - Setting :attr:`shaft_length` will also set :attr:`tip_length`
          to ``1 - shaft_length``.
        - Setting :attr:`tip_length` will also set :attr:`shaft_length`
          to ``1 - tip_length``.

    true_to_scale : bool, default: False
        Alter the shaft and tip geometry so that it's true to scale.

        - If ``True``, the actual shaft and tip radii will be true to the
          values specified by :attr:`shaft_radius` and :attr:`tip_radius`,
          respectively.
        - If ``False``, the actual shaft and tip radii are normalized and
          scaled by :attr:`shaft_length` and :attr:`tip_length`, respectively,
          and the :attr:`total_length` of each axis.

    properties : dict, optional
        Apply any :class:`pyvista.Property` to all axes shafts and tips.

    **kwargs : dict, optional
        Used for handling deprecated parameters.

    See Also
    --------
    pyvista.Plotter.add_axes_marker
        Add a :class:`pyvista.AxesActor` to a scene.

    pyvista.Plotter.add_axes
        Add an axes orientation widget to a scene.

    pyvista.Property
        Surface properties used by the axes shaft and tips.

    pyvista.create_axes_orientation_box
        Create an axes orientation box actor.

    Examples
    --------
    Plot the default axes actor.

    >>> import pyvista as pv
    >>> axes_actor = pv.AxesActor()
    >>> pl = pv.Plotter()
    >>> pl.add_actor(axes_actor)
    (AxesActor (...)
      X label:                    'X'
      Y label:                    'Y'
      Z label:                    'Z'
      Labels off:                 False
      Label position:             (1.0, 1.0, 1.0)
      Shaft type:                 'cylinder'
      Shaft radius:               0.01
      Shaft length:               (0.8, 0.8, 0.8)
      Tip type:                   'cone'
      Tip radius:                 0.4
      Tip length:                 (0.2, 0.2, 0.2)
      Total length:               (1.0, 1.0, 1.0)
      Position:                   (0.0, 0.0, 0.0)
      Scale:                      (1.0, 1.0, 1.0)
      User matrix:                Identity
      Visible:                    True
      X Bounds                    -1.000E+00, 1.000E+00
      Y Bounds                    -1.000E+00, 1.000E+00
      Z Bounds                    -1.000E+00, 1.000E+00, None)
    >>> pl.show()

    Create an axes actor with a specific position and orientation in space.

    >>> axes_actor = pv.AxesActor(
    ...     position=(1, 2, 3), orientation=(10, 20, 30)
    ... )
    >>>
    >>> pl = pv.Plotter()
    >>> _ = pl.add_actor(axes_actor, reset_camera=True)
    >>> _ = pl.show_grid()
    >>> pl.show()

    Create an axes actor with custom colors and axis labels.

    >>> axes_actor = pv.AxesActor(
    ...     labels='UVW',
    ...     shaft_type='line',
    ...     shaft_width=4,
    ...     x_color="#378df0",
    ...     y_color="#ab2e5d",
    ...     z_color="#f7fb9a",
    ...     label_size=(0.1, 0.1),
    ... )
    >>>
    >>> pl = pv.Plotter()
    >>> _ = pl.add_actor(axes_actor)
    >>> pl.show()

    The actor can also be used as a custom orientation widget with
    :func:`~pyvista.Plotter.add_orientation_widget`.

    >>> axes_actor = pv.AxesActor(x_label="U", y_label="V", z_label="W")
    >>>
    >>> pl = pv.Plotter()
    >>> _ = pl.add_mesh(pv.Cone())
    >>> _ = pl.add_orientation_widget(
    ...     axes_actor,
    ...     viewport=(0, 0, 0.5, 0.5),
    ... )
    >>> pl.show()

    """

    # class ShaftType(AnnotatedIntEnum):
    #     """Types of shaft shapes available."""
    #
    #     CYLINDER = (0, "cylinder")
    #     LINE = (1, "line")
    #
    # class TipType(AnnotatedIntEnum):
    #     """Types of tip shapes available."""
    #
    #     CONE = (0, "cone")
    #     SPHERE = (1, "sphere")

    def __init__(
        self,
        x_label='X',
        y_label='Y',
        z_label='Z',
        labels=None,
        label_color=None,
        labels_off=False,
        label_size=(0.25, 0.1),
        label_position=1,
        x_color=None,
        y_color=None,
        z_color=None,
        shaft_type=None,
        shaft_radius=None,
        shaft_width=None,
        shaft_length=None,
        shaft_resolution=None,
        tip_type=None,
        tip_radius=0.4,
        tip_length=None,
        tip_resolution=16,
        total_length=(1, 1, 1),
        position=(0, 0, 0),
        orientation=(0, 0, 0),
        origin=(0, 0, 0),
        scale=(1, 1, 1),
        user_matrix=None,
        visibility=True,
        symmetric_bounds=True,
        auto_shaft_type=True,
        auto_length=True,
        true_to_scale=False,
        properties=None,
        **kwargs,
    ):
        """Initialize AxesActor."""
        # Process kwargs

        # Supported aliases (legacy names from `create_axes_actor`)
        x_label = kwargs.pop('xlabel', x_label)
        y_label = kwargs.pop('ylabel', y_label)
        z_label = kwargs.pop('zlabel', z_label)

        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        cone_radius = kwargs.pop('cone_radius', False)
        if cone_radius:  # pragma: no cover
            warnings.warn(
                "Use of `cone_radius` is deprecated. Use `tip_radius` instead.",
                PyVistaDeprecationWarning,
            )
            tip_radius = cone_radius

        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        line_width = kwargs.pop('line_width', False)
        if line_width:  # pragma: no cover
            warnings.warn(
                "Use of `line_width` is deprecated. Use `shaft_width` instead.",
                PyVistaDeprecationWarning,
            )
            shaft_width = line_width

        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        ambient = kwargs.pop('ambient', None)
        if ambient is not None:  # pragma: no cover
            warnings.warn(
                f"Use of `ambient` is deprecated. Use `properties=dict(ambient={ambient})` instead.",
                PyVistaDeprecationWarning,
            )
            properties = dict(ambient=ambient)

        # Init interface kwargs
        super().__init__(
            x_label=x_label,
            y_label=y_label,
            z_label=z_label,
            labels=labels,
            label_color=label_color,
            labels_off=labels_off,
            label_size=label_size,
            x_color=x_color,
            y_color=y_color,
            z_color=z_color,
            visibility=visibility,
            symmetric_bounds=symmetric_bounds,
            auto_length=auto_length,
            properties=properties,
        )

        # Init geometry props
        # Set flag to prevent updates to the actors
        self._is_init = False

        # Enable workaround to make axes orientable in space.
        # Use undocumented keyword `_make_orientable=False` to disable it
        # and restore the default vtkAxesActor orientation behavior.
        def _init_make_orientable(self, kwargs):
            """Initialize workaround to make axes orientable in space."""
            self._user_matrix = np.eye(4)
            self._cached_matrix = np.eye(4)
            self._update_actor_transformations(reset=True)
            self.__make_orientable = kwargs.pop('_make_orientable', True)
            self._make_orientable = self.__make_orientable

        _init_make_orientable(self, kwargs)

        assert_empty_kwargs(**kwargs)

        # Disable option temporarily for init
        self._auto_shaft_type = False

        # Init interfaced props
        self._init_geometry_params(
            label_position=label_position,
            shaft_type=shaft_type,
            shaft_radius=shaft_radius,
            shaft_length=shaft_length,
            tip_type=tip_type,
            tip_radius=tip_radius,
            tip_length=tip_length,
            total_length=total_length,
            position=position,
            orientation=orientation,
            origin=origin,
            scale=scale,
            user_matrix=user_matrix,
        )

        # Init non-interfaced geometry props
        self.shaft_width = _set_default(shaft_width, 2.0)
        self.shaft_resolution = _set_default(shaft_resolution, 16)
        self.tip_resolution = _set_default(tip_resolution, 16)

        # Set auto shaft type params
        shaft_type_set = False if shaft_type is None else True
        cylinder_params_set = False if shaft_radius is None and shaft_resolution is None else True
        line_params_set = False if shaft_width is None else True

        self._auto_shaft_type = auto_shaft_type
        if auto_shaft_type:
            self._check_auto_shaft_type(shaft_type_set, cylinder_params_set, line_params_set)

        # self._true_to_scale = true_to_scale

        self._update_props()
        self._is_init = True

    def __repr__(self):
        """Representation of the axes actor."""
        if self.user_matrix is None or np.array_equal(self.user_matrix, np.eye(4)):
            mat_info = 'Identity'
        else:
            mat_info = 'Set'

        if self.shaft_type == 'cylinder':
            shaft_param = 'Shaft radius:'
            shaft_value = self.shaft_radius
        else:
            shaft_param = 'Shaft width: '
            shaft_value = self.shaft_width

        bnds = self.bounds

        attr = [
            f"{type(self).__name__} ({hex(id(self))})",
            f"  X label:                    '{self.x_label}'",
            f"  Y label:                    '{self.y_label}'",
            f"  Z label:                    '{self.z_label}'",
            f"  Labels off:                 {self.labels_off}",
            f"  Label position:             {self.label_position}",
            f"  Shaft type:                 '{self.shaft_type}'",
            f"  {shaft_param}               {shaft_value}",
            f"  Shaft length:               {self.shaft_length}",
            f"  Tip type:                   '{self.tip_type}'",
            f"  Tip radius:                 {self.tip_radius}",
            f"  Tip length:                 {self.tip_length}",
            f"  Total length:               {self.total_length}",
            f"  Position:                   {self.position}",
            f"  Scale:                      {self.scale}",
            f"  User matrix:                {mat_info}",
            f"  Visible:                    {self.visibility}",
            f"  X Bounds                    {bnds[0]:.3E}, {bnds[1]:.3E}",
            f"  Y Bounds                    {bnds[2]:.3E}, {bnds[3]:.3E}",
            f"  Z Bounds                    {bnds[4]:.3E}, {bnds[5]:.3E}",
        ]
        return '\n'.join(attr)

    def _init_actors(self, props: Sequence[Property]) -> AxesTuple:
        collection = _vtk.vtkPropCollection()
        self.GetActors(collection)
        actors = [collection.GetItemAsObject(i) for i in range(6)]
        [actor.SetProperty(prop) for actor, prop in zip(actors, props)]
        return AxesTuple(*actors)

    def _init_label_actors(self) -> Tuple[Tuple3D, Tuple3D, Tuple3D]:
        actors = Tuple3D(
            x=self.GetXAxisCaptionActor2D(),
            y=self.GetYAxisCaptionActor2D(),
            z=self.GetZAxisCaptionActor2D(),
        )
        text_setters = Tuple3D(
            x=self.SetXAxisLabelText, y=self.SetYAxisLabelText, z=self.SetZAxisLabelText
        )
        text_getters = Tuple3D(
            x=self.GetXAxisLabelText, y=self.GetYAxisLabelText, z=self.GetZAxisLabelText
        )

        return actors, text_setters, text_getters

    @property
    def true_to_scale(self) -> bool:  # numpydoc ignore=RT01
        """Alter the shaft and tip geometry so that it's true to scale.

        - If ``True``, the rendered shaft and tip radii will be true to the
          values specified by :attr:`shaft_radius` and :attr:`tip_radius`,
          respectively.
        - If ``False``, the rendered shaft and tip radii are normalized by their
          respective lengths, and therefore the actual shaft and tip radii
          are not likely not be true to the values specified by :attr:`shaft_radius`
          and :attr:`tip_radius`, respectively.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor(
        ...     true_to_scale=True, shaft_radius=0.2, tip_radius=0.2
        ... )
        >>> p = pv.Plotter()
        >>> _ = p.show_grid()
        >>> _ = p.add_actor(axes_actor)
        >>> p.show()

        """
        return self._true_to_scale

    @true_to_scale.setter
    def true_to_scale(self, value: bool):  # numpydoc ignore=GL08
        self._true_to_scale = bool(value)

    @property
    def auto_shaft_type(self) -> bool:  # numpydoc ignore=RT01
        """Automatically set the shaft type when setting some properties.

        If ``True``:

        - Setting :attr:`shaft_width` will also set :attr:`shaft_type`
          to ``'line'``.
        - Setting :attr:`shaft_radius` will also set :attr:`shaft_type`
          to ``'cylinder'``.
        - Setting :attr:`shaft_resolution` will also set :attr:`shaft_type`
          to ``'cylinder'``.


        Examples
        --------
        Create an axes actor with cylinder shafts.

        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor(
        ...     shaft_type='cylinder', auto_shaft_type=True
        ... )
        >>> axes_actor.shaft_type
        'cylinder'

        Set the shaft width. The shaft type is automatically adjusted.

        >>> axes_actor.shaft_width = 5
        >>> axes_actor.shaft_width
        5.0
        >>> axes_actor.shaft_type
        'line'

        """
        return self._auto_shaft_type

    @auto_shaft_type.setter
    def auto_shaft_type(self, value: bool):  # numpydoc ignore=GL08
        self._auto_shaft_type = bool(value)

    def _check_auto_shaft_type(self, shaft_type_set, cylinder_params_set, line_params_set):
        # Make sure that we don't auto set with incompatible params
        if shaft_type_set:
            if self.shaft_type == 'line' and cylinder_params_set:
                raise ValueError(
                    "Cannot set properties `shaft_radius` or `shaft_resolution` when shaft type is 'line'\n"
                    "and `auto_shaft_type=True`. Only `shaft_width` can be set."
                )
            elif self.shaft_type == 'cylinder' and line_params_set:
                raise ValueError(
                    "Cannot set `shaft_width` when type is 'cylinder' and `auto_shaft_type=True`.\n"
                    "Only `shaft_radius` or `shaft_resolution` can be set."
                )
        if cylinder_params_set and line_params_set:
            raise ValueError(
                "Cannot set line properties (`shaft_width`) and cylinder properties (`shaft_radius`\n"
                "or `shaft_resolution`) simultaneously when`auto_shaft_type=True`."
            )

    @property
    def symmetric_bounds(self) -> bool:  # numpydoc ignore=RT01
        """Enable or disable symmetry in the axes bounds calculation.

        Calculate the axes bounds as though the axes were symmetric,
        i.e. extended along -X, -Y, and -Z directions. Setting this
        parameter primarily affects camera positioning in a scene.

        - If ``True``, the axes :attr:`bounds` are symmetric about
          its :attr:`position`. Symmetric bounds allow for the axes to rotate
          about its origin, which is useful in cases where the actor
          is used as an orientation widget.

        - If ``False``, the axes :attr:`bounds` are calculated as-is.
          Asymmetric bounds are useful in cases where the axes are
          placed in a scene with other actors, since the symmetry
          could otherwise lead to undesirable camera positioning
          (e.g. camera may be positioned further away than necessary).

        Examples
        --------
        Get the symmetric bounds of the axes.

        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor(symmetric_bounds=True)
        >>> axes_actor.bounds
        (-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
        >>> axes_actor.center
        (0.0, 0.0, 0.0)

        Get the asymmetric bounds.

        >>> axes_actor.symmetric_bounds = False
        >>> axes_actor.bounds  # doctest:+SKIP
        (-0.08, 1.0, -0.08, 1.0, -0.08, 1.0)
        >>> axes_actor.center  # doctest:+SKIP
        (0.46, 0.46, 0.46)

        Show the difference in camera positioning with and without
        symmetric bounds. Orientation is added for visualization.

        >>> # Create actors
        >>> axes_actor_sym = pv.AxesActor(
        ...     orientation=(90, 0, 0), symmetric_bounds=True
        ... )
        >>> axes_actor_asym = pv.AxesActor(
        ...     orientation=(90, 0, 0), symmetric_bounds=False
        ... )
        >>>
        >>> # Show multi-window plot
        >>> pl = pv.Plotter(shape=(1, 2))
        >>> pl.subplot(0, 0)
        >>> _ = pl.add_text("Symmetric axes")
        >>> _ = pl.add_actor(axes_actor_sym)
        >>> pl.subplot(0, 1)
        >>> _ = pl.add_text("Asymmetric axes")
        >>> _ = pl.add_actor(axes_actor_asym)
        >>> pl.show()

        """
        return self._symmetric_bounds

    @symmetric_bounds.setter
    def symmetric_bounds(self, value: bool):  # numpydoc ignore=GL08
        self._symmetric_bounds = bool(value)

    @property
    def _visibility(self) -> bool:  # numpydoc ignore=RT01
        """Enable or disable the visibility of the axes.

        Examples
        --------
        Create an AxesActor and check its visibility

        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.visibility
        True

        """
        return bool(self.GetVisibility())

    @_visibility.setter
    def _visibility(self, value: bool):  # numpydoc ignore=GL08
        self.SetVisibility(value)

    @property
    def _total_length(self) -> Tuple[float, float, float]:  # numpydoc ignore=RT01
        """Total length of each axis (shaft plus tip).

        Values must be non-negative.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.total_length
        (1.0, 1.0, 1.0)
        >>> axes_actor.total_length = 1.2
        >>> axes_actor.total_length
        (1.2, 1.2, 1.2)
        >>> axes_actor.total_length = (1.0, 0.9, 0.5)
        >>> axes_actor.total_length
        (1.0, 0.9, 0.5)

        """
        return self.GetTotalLength()

    @_total_length.setter
    def _total_length(self, length: Vector):  # numpydoc ignore=GL08
        self.SetTotalLength(length)

    @property
    def _shaft_length(self) -> Tuple[float, float, float]:  # numpydoc ignore=RT01
        """Normalized length of the shaft for each axis.

        Values must be in range ``[0, 1]``.

        Notes
        -----
        Setting this property will automatically change the :attr:`tip_length` to
        ``1 - shaft_length`` if :attr:`auto_shaft_type` is ``True``.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.shaft_length
        (0.8, 0.8, 0.8)
        >>> axes_actor.shaft_length = 0.7
        >>> axes_actor.shaft_length
        (0.7, 0.7, 0.7)
        >>> axes_actor.shaft_length = (1.0, 0.9, 0.5)
        >>> axes_actor.shaft_length
        (1.0, 0.9, 0.5)

        """
        return self.GetNormalizedShaftLength()

    @_shaft_length.setter
    def _shaft_length(self, length: Vector):  # numpydoc ignore=GL08
        self.SetNormalizedShaftLength(length)

    @property
    def _tip_length(self) -> Tuple[float, float, float]:  # numpydoc ignore=RT01
        """Normalized length of the tip for each axis.

        Values must be in range ``[0, 1]``.

        Notes
        -----
        Setting this property will automatically change the :attr:`shaft_length` to
        ``1 - tip_length`` if :attr:`auto_shaft_type` is ``True``.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.tip_length
        (0.2, 0.2, 0.2)
        >>> axes_actor.tip_length = 0.3
        >>> axes_actor.tip_length
        (0.3, 0.3, 0.3)
        >>> axes_actor.tip_length = (0.1, 0.4, 0.2)
        >>> axes_actor.tip_length
        (0.1, 0.4, 0.2)

        """
        return self.GetNormalizedTipLength()

    @_tip_length.setter
    def _tip_length(self, length: Vector):  # numpydoc ignore=GL08
        self.SetNormalizedTipLength(length)

    @property
    def _label_position(self) -> Tuple[float, float, float]:  # numpydoc ignore=RT01
        """Normalized position of the text label along each axis.

        Values must be non-negative.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.label_position
        (1.0, 1.0, 1.0)
        >>> axes_actor.label_position = 0.3
        >>> axes_actor.label_position
        (0.3, 0.3, 0.3)
        >>> axes_actor.label_position = (0.1, 0.4, 0.2)
        >>> axes_actor.label_position
        (0.1, 0.4, 0.2)

        """
        return self.GetNormalizedLabelPosition()

    @_label_position.setter
    def _label_position(self, position: Vector):  # numpydoc ignore=GL08
        self.SetNormalizedLabelPosition(position)

    @property
    def tip_resolution(self) -> int:  # numpydoc ignore=RT01
        """Resolution of the axes tips.

        Value must be a positive integer.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.tip_resolution
        16
        >>> axes_actor.tip_resolution = 24
        >>> axes_actor.tip_resolution
        24

        """
        # Get cone resolution and assume value is the same for sphere
        return self.GetConeResolution()

    @tip_resolution.setter
    def tip_resolution(self, resolution: int):  # numpydoc ignore=GL08
        self.SetConeResolution(resolution)
        self.SetSphereResolution(resolution)
        _check_range(resolution, (1, float('inf')), 'tip_resolution')

    @property
    def cone_resolution(self) -> int:  # numpydoc ignore=RT01
        """Resolution of the axes cone tips.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`tip_resolution` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `cone_resolution` is deprecated. Use `tip_resolution` instead.",
            PyVistaDeprecationWarning,
        )
        return self.tip_resolution

    @cone_resolution.setter
    def cone_resolution(self, resolution: int):  # numpydoc ignore=GL08
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `cone_resolution` is deprecated. Use `tip_resolution` instead.",
            PyVistaDeprecationWarning,
        )
        self.tip_resolution = resolution

    @property
    def sphere_resolution(self) -> int:  # numpydoc ignore=RT01
        """Resolution of the axes sphere tips.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`tip_resolution` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `sphere_resolution` is deprecated. Use `tip_resolution` instead.",
            PyVistaDeprecationWarning,
        )
        return self.tip_resolution

    @sphere_resolution.setter
    def sphere_resolution(self, resolution: int):  # numpydoc ignore=GL08
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `sphere_resolution` is deprecated. Use `tip_resolution` instead.",
            PyVistaDeprecationWarning,
        )
        self.tip_resolution = resolution

    @property
    def shaft_resolution(self) -> int:  # numpydoc ignore=RT01
        """Resolution of the axes shafts.

        Value must be a positive integer.

        Notes
        -----
        Setting this property will automatically change the :attr:`shaft_type` to
        ``'cylinder'`` if :attr:`auto_shaft_type` is ``True``.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.shaft_resolution
        16
        >>> axes_actor.shaft_resolution = 24
        >>> axes_actor.shaft_resolution
        24

        """
        return self.GetCylinderResolution()

    @shaft_resolution.setter
    def shaft_resolution(self, resolution: int):  # numpydoc ignore=GL08
        if self.auto_shaft_type:
            self.SetShaftTypeToCylinder()

        self.SetCylinderResolution(resolution)
        _check_range(resolution, (1, float('inf')), 'shaft_resolution')

    @property
    def cylinder_resolution(self) -> int:  # numpydoc ignore=RT01
        """Cylinder resolution of the axes shafts.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`shaft_resolution` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `cylinder_resolution` is deprecated. Use `shaft_resolution` instead.",
            PyVistaDeprecationWarning,
        )
        return self.shaft_resolution

    @cylinder_resolution.setter
    def cylinder_resolution(self, res: int):  # numpydoc ignore=GL08
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `cylinder_resolution` is deprecated. Use `shaft_resolution` instead.",
            PyVistaDeprecationWarning,
        )
        self.SetCylinderResolution(res)

    @property
    def tip_radius(self) -> float:  # numpydoc ignore=RT01
        """Radius of the axes tips.

        Value must be non-negative.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.tip_radius
        0.4
        >>> axes_actor.tip_radius = 0.8
        >>> axes_actor.tip_radius
        0.8

        """
        # Get cone radius and assume value is the same for sphere
        return self.GetConeRadius()

    @tip_radius.setter
    def tip_radius(self, radius: float):  # numpydoc ignore=GL08
        is_modified = self.GetConeRadius() != radius and self.GetSphereRadius() != radius
        self.SetConeRadius(radius)
        self.SetSphereRadius(radius)
        _check_range(radius, (0, float('inf')), 'tip_radius')

        if is_modified:
            # need to update internal mapper (ConeSource or SphereSource)
            self.Modified()
            self._update_props()

    @property
    def cone_radius(self) -> float:  # numpydoc ignore=RT01
        """Radius of the axes cone tips.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`tip_radius` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `cone_radius` is deprecated. Use `tip_radius` instead.",
            PyVistaDeprecationWarning,
        )
        return self.tip_radius

    @cone_radius.setter
    def cone_radius(self, radius: float):  # numpydoc ignore=GL08
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `cone_radius` is deprecated. Use `tip_radius` instead.",
            PyVistaDeprecationWarning,
        )
        self.tip_radius = radius

    @property
    def sphere_radius(self) -> float:  # numpydoc ignore=RT01
        """Radius of the axes sphere tips.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`tip_radius` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `sphere_radius` is deprecated. Use `tip_radius` instead.",
            PyVistaDeprecationWarning,
        )
        return self.tip_radius

    @sphere_radius.setter
    def sphere_radius(self, radius: float):  # numpydoc ignore=GL08
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `sphere_radius` is deprecated. Use `tip_radius` instead.",
            PyVistaDeprecationWarning,
        )
        self.tip_radius = radius

    @property
    def cylinder_radius(self) -> float:  # numpydoc ignore=RT01
        """Cylinder radius of the axes shafts.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`shaft_radius` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `cylinder_radius` is deprecated. Use `shaft_radius` instead.",
            PyVistaDeprecationWarning,
        )
        return self.shaft_radius

    @cylinder_radius.setter
    def cylinder_radius(self, radius: float):  # numpydoc ignore=GL08
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `cylinder_radius` is deprecated. Use `shaft_radius` instead.",
            PyVistaDeprecationWarning,
        )
        self.shaft_radius = radius

    @property
    def _shaft_radius(self):  # numpydoc ignore=RT01
        """Cylinder radius of the axes shafts.

        Value must be non-negative.

        Notes
        -----
        Setting this property will automatically change the ``shaft_type`` to
        ``'cylinder'`` if :attr:`auto_shaft_type` is ``True``.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.shaft_radius
        0.01
        >>> axes_actor.shaft_radius = 0.03
        >>> axes_actor.shaft_radius
        0.03

        """
        return self.GetCylinderRadius()

    @_shaft_radius.setter
    def _shaft_radius(self, radius):  # numpydoc ignore=GL08
        do_update = self.shaft_type == 'cylinder' and radius != self.GetCylinderRadius()

        self.SetCylinderRadius(radius)

        if self.auto_shaft_type:
            self.SetShaftTypeToCylinder()

        if do_update:
            # Need to update internal CylinderSource mapper
            self._update_props()

    @property
    def shaft_width(self):  # numpydoc ignore=RT01
        """Line width of the axes shafts in screen units.

        Value must be non-negative.

        Notes
        -----
        Setting this property will automatically change the :attr:`shaft_type` to
        ``'line'`` if :attr:`auto_shaft_type` is ``True``.

        """
        # Get x width and assume width is the same for each x, y, and z
        return self.GetXAxisShaftProperty().GetLineWidth()

    @shaft_width.setter
    def shaft_width(self, width):  # numpydoc ignore=GL08
        if self.auto_shaft_type:
            self.SetShaftTypeToLine()

        self.GetXAxisShaftProperty().SetLineWidth(width)
        self.GetYAxisShaftProperty().SetLineWidth(width)
        self.GetZAxisShaftProperty().SetLineWidth(width)
        _check_range(width, (0, float('inf')), 'shaft_width')

    @property
    def _shaft_type(self) -> str:  # numpydoc ignore=RT01
        """Tip type for all axes.

        Can be a cylinder (``0`` or ``'cylinder'``) or a line (``1`` or ``'line'``).

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.shaft_type = "line"
        >>> axes_actor.shaft_type
        'line'

        """
        t = self.GetShaftType()
        if t == 0:
            return 'cylinder'
        elif t == 1:
            return 'line'
        else:
            raise NotImplementedError("Only 'cylinder' and 'line' tip types are supported.")

    @_shaft_type.setter
    def _shaft_type(self, shaft_type: str):  # numpydoc ignore=GL08
        if shaft_type == 'cylinder':
            self.SetShaftTypeToCylinder()
        elif shaft_type == 'line':
            self.SetShaftTypeToLine()
        else:
            raise ValueError(f"Shaft type must be 'cylinder' or 'line'. Got {shaft_type} instead.")

    @property
    def _tip_type(self) -> str:  # numpydoc ignore=RT01
        """Tip type for all axes.

        Can be a cone (``0`` or ``'cone'``) or a sphere (``1`` or ``'sphere'``).

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.tip_type = 'sphere'
        >>> axes_actor.tip_type
        'sphere'

        """
        t = self.GetTipType()
        if t == 0:
            return 'cone'
        elif t == 1:
            return 'sphere'
        else:
            raise NotImplementedError("Only 'cone' and 'sphere' tip types are supported.")

    @_tip_type.setter
    def _tip_type(self, tip_type: str):  # numpydoc ignore=GL08
        if tip_type == 'cone':
            self.SetTipTypeToCone()
        elif tip_type == 'sphere':
            self.SetTipTypeToSphere()

    @property
    def x_axis_label(self) -> str:  # numpydoc ignore=RT01
        """Text label for the x-axis.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`x_label` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `x_axis_label` is deprecated. Use `x_label` instead.",
            PyVistaDeprecationWarning,
        )
        return self.x_label

    @x_axis_label.setter
    def x_axis_label(self, label: str):  # numpydoc ignore=GL08
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `x_axis_label` is deprecated. Use `x_label` instead.",
            PyVistaDeprecationWarning,
        )
        self.x_label = label

    @property
    def y_axis_label(self) -> str:  # numpydoc ignore=RT01
        """Text label for the y-axis.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`y_label` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `y_axis_label` is deprecated. Use `y_label` instead.",
            PyVistaDeprecationWarning,
        )
        return self.y_label

    @y_axis_label.setter
    def y_axis_label(self, label: str):  # numpydoc ignore=GL08
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `y_axis_label` is deprecated. Use `y_label` instead.",
            PyVistaDeprecationWarning,
        )
        self.y_label = label

    @property
    def z_axis_label(self) -> str:  # numpydoc ignore=RT01
        """Text label for the z-axis.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`z_label` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `z_axis_label` is deprecated. Use `z_label` instead.",
            PyVistaDeprecationWarning,
        )
        return self.z_label

    @z_axis_label.setter
    def z_axis_label(self, label: str):  # numpydoc ignore=GL08
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `z_axis_label` is deprecated. Use `z_label` instead.",
            PyVistaDeprecationWarning,
        )
        self.z_label = label

    @property
    def x_axis_shaft_properties(self):  # numpydoc ignore=RT01
        """:class:`~pyvista.ActorProperties` of the x-axis shaft.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`x_shaft_prop` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `x_axis_shaft_properties` is deprecated. Use `x_shaft_prop` instead.",
            PyVistaDeprecationWarning,
        )
        return ActorProperties(self.GetXAxisShaftProperty())

    @property
    def y_axis_shaft_properties(self):  # numpydoc ignore=RT01
        """:class:`~pyvista.ActorProperties` of the y-axis shaft.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`y_shaft_prop` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `y_axis_shaft_properties` is deprecated. Use `y_shaft_prop` instead.",
            PyVistaDeprecationWarning,
        )
        return ActorProperties(self.GetYAxisShaftProperty())

    @property
    def z_axis_shaft_properties(self):  # numpydoc ignore=RT01
        """:class:`~pyvista.ActorProperties` of the z-axis shaft.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`z_shaft_prop` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `z_axis_shaft_properties` is deprecated. Use `z_shaft_prop` instead.",
            PyVistaDeprecationWarning,
        )
        return ActorProperties(self.GetZAxisShaftProperty())

    @property
    def x_axis_tip_properties(self):  # numpydoc ignore=RT01
        """:class:`~pyvista.ActorProperties` of the x-axis tip.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`x_tip_prop` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `x_axis_tip_properties` is deprecated. Use `x_tip_prop` instead.",
            PyVistaDeprecationWarning,
        )
        return ActorProperties(self.GetXAxisTipProperty())

    @property
    def y_axis_tip_properties(self):  # numpydoc ignore=RT01
        """:class:`~pyvista.ActorProperties` of the y-axis tip.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`y_tip_prop` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `y_axis_tip_properties` is deprecated. Use `y_tip_prop` instead.",
            PyVistaDeprecationWarning,
        )
        return ActorProperties(self.GetYAxisTipProperty())

    @property
    def z_axis_tip_properties(self):  # numpydoc ignore=RT01
        """:class:`~pyvista.ActorProperties` of the z-axis tip.

        .. deprecated:: 0.43.0

            This parameter is deprecated. Use :attr:`z_tip_prop` instead.

        """
        # deprecated 0.43.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            "Use of `z_axis_tip_properties` is deprecated. Use `z_tip_prop` instead.",
            PyVistaDeprecationWarning,
        )
        return ActorProperties(self.GetZAxisTipProperty())

    @property
    def labels_off(self) -> bool:  # numpydoc ignore=RT01
        """Enable or disable the text labels for the axes."""
        return not bool(self.GetAxisLabels())

    @labels_off.setter
    def labels_off(self, value: bool):  # numpydoc ignore=GL08
        self.SetAxisLabels(not value)

    @wraps(_vtk.vtkAxesActor.GetBounds)
    def GetBounds(self) -> BoundsLike:  # numpydoc ignore=RT01,GL08
        """Wrap method to make axes orientable in space."""
        if self._make_orientable:
            # GetBounds() defined by vtkAxesActor accesses a protected
            # self.Bounds property which is hard-coded to be centered
            # and symmetric about the origin.However, since the axes
            # are made orientable, we instead compute the bounds from
            # the actual shaft and tip actor bounds.

            # NOTE: Overriding GetBounds() only works for python methods
            # that call GetBounds(). It has no effect on compiled vtk
            # code which directly calls vtkAxesActor.GetBounds().This
            # can result in camera issues when rendering a scene since
            # vtkRenderer.ComputeVisiblePropBounds() uses GetBounds()
            # of all actors when resetting the camera, which will not
            # execute this override.
            return self._compute_actor_bounds()
        return super().GetBounds()

    @wraps(_vtk.vtkProp3D.GetCenter)
    def GetCenter(self):  # numpydoc ignore=RT01,GL08
        """Wrap method to make axes orientable in space."""
        if self._make_orientable:
            b = self.bounds
            return (b[1] + b[0]) / 2, (b[3] + b[2]) / 2, (b[5] + b[4]) / 2
        return super().GetCenter()

    @wraps(_vtk.vtkProp3D.GetLength)
    def GetLength(self):  # numpydoc ignore=RT01,GL08
        """Wrap method to make axes orientable in space."""
        if self._make_orientable:
            length = 0
            bnds = self.bounds
            for i in range(3):
                diff = bnds[2 * i + 1] - bnds[2 * i]
                length += diff * diff
            return length**0.5
        return super().GetLength()

    @wraps(_vtk.vtkProp3D.RotateX)
    def RotateX(self, *args):  # numpydoc ignore=RT01,PR01
        """Wrap method to make axes orientable in space."""
        super().RotateX(*args)
        self._update_actor_transformations()

    @wraps(_vtk.vtkProp3D.RotateY)
    def RotateY(self, *args):  # numpydoc ignore=RT01,PR01
        """Wrap method to make axes orientable in space."""
        super().RotateY(*args)
        self._update_actor_transformations()

    @wraps(_vtk.vtkProp3D.RotateZ)
    def RotateZ(self, *args):  # numpydoc ignore=RT01,PR01
        """Wrap method to make axes orientable in space."""
        super().RotateZ(*args)
        self._update_actor_transformations()

    @wraps(_vtk.vtkProp3D.SetScale)
    def SetScale(self, *args):  # numpydoc ignore=RT01,PR01
        """Wrap method to make axes orientable in space."""
        super().SetScale(*args)
        self._update_actor_transformations()

    @wraps(_vtk.vtkProp3D.SetOrientation)
    def SetOrientation(self, *args):  # numpydoc ignore=RT01,PR01
        """Wrap method to make axes orientable in space."""
        super().SetOrientation(*args)
        self._update_actor_transformations()

    @wraps(_vtk.vtkProp3D.SetOrigin)
    def SetOrigin(self, *args):  # numpydoc ignore=RT01,PR01
        """Wrap method to make axes orientable in space."""
        super().SetOrigin(*args)
        self._update_actor_transformations()

    @wraps(_vtk.vtkProp3D.SetPosition)
    def SetPosition(self, *args):  # numpydoc ignore=RT01,PR01
        """Wrap method to make axes orientable in space."""
        super().SetPosition(*args)
        self._update_actor_transformations()

    @wraps(_vtk.vtkAxesActor.SetNormalizedShaftLength)
    def SetNormalizedShaftLength(self, *args):  # numpydoc ignore=RT01,PR01
        """Wrap method to make axes orientable in space."""
        super().SetNormalizedShaftLength(*args)
        self._update_actor_transformations()

    @wraps(_vtk.vtkAxesActor.SetNormalizedTipLength)
    def SetNormalizedTipLength(self, *args):  # numpydoc ignore=RT01,PR01
        """Wrap method to make axes orientable in space."""
        super().SetNormalizedTipLength(*args)
        self._update_actor_transformations()

    @wraps(_vtk.vtkAxesActor.SetTotalLength)
    def SetTotalLength(self, *args):  # numpydoc ignore=RT01,PR01
        """Wrap method to make axes orientable in space."""
        super().SetTotalLength(*args)
        self._update_actor_transformations()

    @wraps(_vtk.vtkProp3D.GetUserMatrix)
    def GetUserMatrix(self):  # numpydoc ignore=RT01,PR01
        """Wrap method to make axes orientable in space."""
        if self._make_orientable:
            self._user_matrix = np.eye(4) if self._user_matrix is None else self._user_matrix
            return vtkmatrix_from_array(self._user_matrix)
        else:
            matrix = super().GetUserMatrix()
            self._user_matrix = array_from_vtkmatrix(matrix)
            return matrix

    @wraps(_vtk.vtkProp3D.SetUserMatrix)
    def SetUserMatrix(self, *args):  # numpydoc ignore=RT01,PR01
        """Wrap method to make axes orientable in space."""
        super().SetUserMatrix(*args)
        self._user_matrix = array_from_vtkmatrix(*args)
        self._update_actor_transformations()

    @property
    def _implicit_matrix(self) -> Union[np.ndarray, _vtk.vtkMatrix4x4]:  # numpydoc ignore=GL08
        """Compute the transformation matrix implicitly defined by 3D parameters."""
        return self._compute_scaled_implicit_matrix(scale=(1, 1, 1))

    def _compute_true_to_scale_factors(self) -> np.ndarray:
        """Compute radial scale factors for axes shaft and tip actors.

        The scaling factors can be applied to the actors to make it so
        the actual shaft and tip radii will be equal to the shaft and
        tip radius property values.

        NOTE: This function assumes the actors have no transformations
        applied. The calling function should remove any transformations
        beforehand, and re-apply them afterward.
        """

        def reciprocal(x):
            # Calc reciprocal and avoid division by zero
            tol = 1e-8
            nonzero = np.logical_or(x > tol, x < tol)
            x[nonzero] = np.reciprocal(x[nonzero])
            x[~nonzero] = 0
            return x

        diag = np.eye(3, dtype=bool)
        off_diag = np.logical_not(diag)

        # Compute actor sizes
        bounds = [actor.GetBounds() for actor in self._actors]
        size = np.array([[b[1] - b[0], b[3] - b[2], b[5] - b[4]] for b in bounds])

        # Get scale factors which will normalize sizes to unity
        scales = reciprocal(size)

        # Create views for processing
        shaft_scale = size[:3]
        tip_scale = size[3:6]

        # Scale radially by the diameter
        shaft_scale[off_diag] *= self.shaft_radius * 2
        tip_scale[off_diag] *= self.tip_radius * 2

        # Do not scale axially, only radially
        shaft_scale[diag] = 1
        tip_scale[diag] = 1

        return scales

    def _update_actor_transformations(self, reset=False):  # numpydoc ignore=RT01,PR01
        if not self._is_init:
            return

        if reset:
            matrix = np.eye(4)
        elif self.__make_orientable:
            matrix = self._concatenate_implicit_matrix_and_user_matrix()
        else:
            return

        if not np.array_equal(matrix, self._cached_matrix) or reset:
            if np.array_equal(matrix, np.eye(4)):
                self.UseBoundsOn()
            else:
                # Calls to vtkRenderer.ResetCamera() will use the
                # incorrect axes bounds if a transformation is applied.
                # As a workaround, set UseBoundsOff(). In some cases,
                # this will require manual adjustment of the camera
                # from the user.
                self.UseBoundsOff()

            self._cached_matrix = matrix
            matrix = vtkmatrix_from_array(matrix)
            super().SetUserMatrix(matrix)
            [actor.SetUserMatrix(matrix) for actor in self._actors]

    def _concatenate_implicit_matrix_and_user_matrix(self, scale=(1, 1, 1)) -> np.ndarray:
        """Get transformation matrix similar to vtkProp3D::GetMatrix().

        Additional scaling may be passed to the implicit matrix.
        """
        return self._user_matrix @ self._compute_scaled_implicit_matrix(scale)

    def _compute_actor_bounds(self) -> BoundsLike:
        """Compute symmetric axes bounds from the shaft and tip actors."""
        all_bounds = np.zeros((12, 3))
        for i, a in enumerate(self._actors):
            bnds = a.GetBounds()
            all_bounds[i] = bnds[0::2]
            all_bounds[i + 6] = bnds[1::2]

        if self.symmetric_bounds:
            # Append the same bounds, but inverted around the axes position
            # to mimic having symmetric axes. The position may be moved with
            # `user_matrix`, so apply the transform to position.
            position = (self._user_matrix @ np.append(self.GetPosition(), 1))[:3]
            all_bounds = np.vstack((all_bounds, 2 * position - all_bounds))

        xmin, xmax = np.min(all_bounds[:, 0]), np.max(all_bounds[:, 0])
        ymin, ymax = np.min(all_bounds[:, 1]), np.max(all_bounds[:, 1])
        zmin, zmax = np.min(all_bounds[:, 2]), np.max(all_bounds[:, 2])
        return xmin, xmax, ymin, ymax, zmin, zmax

    def _compute_scaled_implicit_matrix(
        self, scale: Sequence[float] = (1.0, 1.0, 1.0)
    ) -> np.ndarray:
        old_scale = self.GetScale()
        new_scale = old_scale[0] * scale[0], old_scale[1] * scale[1], old_scale[2] * scale[2]
        temp_actor = _vtk.vtkActor()
        temp_actor.SetOrigin(*self.GetOrigin())
        temp_actor.SetScale(*new_scale)
        temp_actor.SetPosition(*self.GetPosition())
        temp_actor.SetOrientation(*self.GetOrientation())
        return array_from_vtkmatrix(temp_actor.GetMatrix())

    def _update_props(self):
        """Trigger a call to protected vtk method vtkAxesActor::UpdateProps()."""
        # Get a property and modify its value
        delta = 1e-8
        val = list(self.shaft_length)
        temp_val = val.copy()
        if temp_val[0] > delta:
            temp_val[0] -= delta
        else:
            temp_val[0] += delta

        # Change value to trigger update
        self.SetNormalizedShaftLength(temp_val)
        self.SetNormalizedShaftLength(val)

        self._update_actor_transformations()

    @property
    def _make_orientable(self) -> bool:
        return self.__make_orientable

    @_make_orientable.setter
    def _make_orientable(self, value: bool):
        self.__make_orientable = value
        self._update_actor_transformations(reset=not value)


class AxesAssembly(_AxesProp, _vtk.vtkPropAssembly):
    """Assembly of axes actors."""

    def _init_actors(self, props: Sequence[Property]) -> AxesTuple:
        # Use pyvista namespace to avoid circular import
        actors = [pyvista.Actor(prop) for prop in props]
        [self.AddPart(actor) for actor in actors]
        return AxesTuple(*actors)

    def _init_label_actors(self) -> Tuple[Tuple3D, Tuple3D, Tuple3D]:
        actors = Tuple3D(
            x=_vtk.vtkCaptionActor2D(),
            y=_vtk.vtkCaptionActor2D(),
            z=_vtk.vtkCaptionActor2D(),
        )
        [self.AddPart(actor) for actor in actors]

        setters = Tuple3D(
            x=lambda val: actors.x.SetInput(val),
            y=lambda val: actors.y.SetInput(val),
            z=lambda val: actors.z.SetInput(val),
        )
        getters = Tuple3D(
            x=actors.x.GetInput(),
            y=actors.y.GetInput(),
            z=actors.z.GetInput(),
        )

        return actors, setters, getters

    # @property
    # def _total_length(self):
    #     ...
    #
    # @property
    # def _shaft_length(self):
    #     ...
    #
    # @property
    # def _tip_length(self):
    #     ...
    #
    # @property
    # def _label_position(self):
    #     ...
    #
    # @property
    # def _tip_radius(self):
    #     ...
    #
    # @property
    # def _shaft_type(self):
    #     ...
    #
    # @property
    # def _tip_type(self):
    #     ...


def _set_default(val, default):
    return default if val is None else val
