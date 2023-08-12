from typing import Optional
from PyQt6 import QtCore, QtGui, QtWidgets
from enum import Enum

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from _2d_animation import Animation2D
from _3d_animation import Animation3D
from components import OrbitSimSettings, ViewTypePicker, SettingsKeys, ViewType, SettingsBtnLayout, \
    HorizontalValuePicker, ValueViewer, VerticalValuePicker, StarSystem, solar_system_enum_to_class
import matplotlib

from spiro_animation import SpiroAnimation

matplotlib.use('TkAgg')

PLANETS: list[str] = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]


class PageIndexes(Enum):
    ORBITS_PAGE = 0
    ORBITS_PAGE_SETTINGS = 1
    SPIROGRAPH_PAGE = 2


class OrbitsPage(QtWidgets.QWidget):
    ORBITS_STATS: dict[str, Optional[str]] = {
        "Coordinates": None,
        "Mass": None,
        "Angular velocity": None,
        "Linear velocity": None,
        "Distance from centre": None,
        "Orbital angle": None,
        "Eccentricity": None,
        "Semi-major axis": None,
        "Semi-minor axis": None,
        "Orbital period": None,
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setParent(parent)
        root_layout = QtWidgets.QHBoxLayout()
        self.sim_settings = OrbitSimSettings()
        #
        # Creating the graph canvas and the toolbar to manipulate it
        #
        self.fig = Figure(figsize=(10, 10))
        self.canvas = FigureCanvas(self.fig)
        self.graph_layout = QtWidgets.QVBoxLayout()
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.graph_layout.addWidget(self.toolbar)
        self.graph_layout.addWidget(self.canvas)
        settings_btn_layout = SettingsBtnLayout(on_click=self.on_settings_button_click,
                                                btn_width=30,
                                                btn_height=30)
        self.graph_layout.addLayout(settings_btn_layout)
        root_layout.addLayout(self.graph_layout)
        self.anim = None
        self.display_animation()
        # self.anim = Animation2D(self.fig, "SOLAR_SYSTEM", ["VENUS", "EARTH"], 10, 700, 0.1)
        #
        # Creating layout and widgets for user to pick planet to see orbit stats on
        #
        self.planet_picker_layout = HorizontalValuePicker(
            lbl_text="Planet: ",
            value_type="from_multiple",
            default_val="Earth",
            choices=PLANETS,
            tooltip="Choose the name of the planet to see orbit stats on",
            on_change=self.on_planet_dropdown_changed,
            fixed_lbl_width=50,
            fixed_form_width=150
        )
        #
        # Creating layout and widgets to display planet orbit stats
        #
        stats_layout = QtWidgets.QGridLayout()
        self.stats_components: list[ValueViewer] = []
        for i, orbit_stat in enumerate(OrbitsPage.ORBITS_STATS.keys()):
            stat_name, stat_value = orbit_stat, OrbitsPage.ORBITS_STATS[orbit_stat]
            stats_component = ValueViewer(stat_name,
                                          stat_value,
                                          fixed_width=150,
                                          fixed_key_height=20,
                                          fixed_value_height=35,
                                          alignment=QtCore.Qt.AlignmentFlag.AlignTop)
            self.stats_components.append(stats_component)
            stats_layout.addLayout(stats_component, i // 2, i % 2, 1, 1)
        #
        # Appending these widgets to a wrapper layout
        #
        controls_layout = QtWidgets.QVBoxLayout()
        controls_layout.addStretch()
        controls_layout.addLayout(self.planet_picker_layout)
        controls_layout.addSpacing(10)
        controls_layout.addLayout(stats_layout)
        controls_layout.addStretch()
        controls_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.addLayout(controls_layout)
        #
        # Displaying the root layout containing all the widgets of the orbit page
        #
        self.setLayout(root_layout)

    def on_planet_dropdown_changed(self, new_index: int):
        new_planet: str = PLANETS[new_index]
        print("NEW PLANET: ", new_planet)
        # TODO: add binding to engine to set new stats on the new planet
        pass

    def on_settings_button_click(self):
        self.parent.switch_to(PageIndexes.ORBITS_PAGE_SETTINGS.value)

    def update_graph(self):
        print("NEW SETTINGS")
        print(self.sim_settings.SETTINGS)
        # Called when simulation settings have been updated
        self.planet_picker_layout.set_choices(self.sim_settings.SETTINGS[SettingsKeys.OBJECTS_TO_SHOW.value], 0)
        self.display_animation()
        pass

    def set_stats(self, new_stats: dict[str, str]):
        assert len(new_stats) == len(OrbitsPage.ORBITS_STATS)
        for i, k in enumerate(new_stats.keys()):
            OrbitsPage.ORBITS_STATS[k] = new_stats[k]
            self.stats_components[i].set_text(new_stats[k])

    def display_animation(self):
        settings = self.sim_settings.SETTINGS
        solar_system = settings[SettingsKeys.STAR_SYSTEM.value]
        solar_system_class = solar_system_enum_to_class[solar_system]

        centre = solar_system_class.Planet(settings[SettingsKeys.CENTRE_OF_ORBIT.value]).name
        planets = [solar_system_class.Planet(s).name for s in settings[SettingsKeys.OBJECTS_TO_SHOW.value]]
        orbit_duration = int(settings[SettingsKeys.ORBIT_TIME.value])
        num_orbits = int(settings[SettingsKeys.NUM_ORBITS.value])
        if self.anim:
            self.anim.ani.event_source.stop()
        self.graph_layout.removeWidget(self.canvas)
        self.graph_layout.removeWidget(self.toolbar)
        self.fig = Figure(figsize=(10, 10))
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.graph_layout.insertWidget(0, self.toolbar)
        self.graph_layout.insertWidget(1, self.canvas)
        args = [self.fig, solar_system.name, planets, centre, orbit_duration, num_orbits]
        print("ANIM PARAMS", args)
        if settings[SettingsKeys.VIEW_TYPE.value] == ViewType.TWO_D.value:
            self.anim = Animation2D(*args)
        else:
            self.anim = Animation3D(*args[:-1])


class OrbitsPageSettings(QtWidgets.QWidget):
    OBJECTS_TO_SHOW_OPTIONS: list[str]
    CENTRE_OF_ORBIT_OPTIONS: list[str]
    PLANET_STAT_OPTIONS: list[str]

    def __init__(self, parent):
        super().__init__()
        self.child_widgets = []
        self.parent = parent
        self.settings = OrbitSimSettings()
        self.original_settings: dict = {
            SettingsKeys.STAR_SYSTEM.value: StarSystem.SOLAR_SYSTEM,
            SettingsKeys.CENTRE_OF_ORBIT.value: solar_system_enum_to_class[StarSystem.SOLAR_SYSTEM].Planet[solar_system_enum_to_class[StarSystem.SOLAR_SYSTEM].SUN].value,
            SettingsKeys.OBJECTS_TO_SHOW.value: [e.value for e in solar_system_enum_to_class[StarSystem.SOLAR_SYSTEM].Planet if e.name != "SUN"],
            SettingsKeys.ORBIT_TIME.value: 1,
            SettingsKeys.VIEW_TYPE.value: ViewType.TWO_D.value,
            SettingsKeys.NUM_ORBITS.value: 1,
        }
        OrbitsPageSettings.OBJECTS_TO_SHOW_OPTIONS = self.original_settings[SettingsKeys.OBJECTS_TO_SHOW.value]
        OrbitsPageSettings.CENTRE_OF_ORBIT_OPTIONS = [e.value for e in solar_system_enum_to_class[StarSystem.SOLAR_SYSTEM].Planet]
        root_layout = QtWidgets.QVBoxLayout()
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        reset_button = QtWidgets.QPushButton("Reset")
        reset_button.clicked.connect(self.on_reset_button_pressed)
        reset_button.setFixedWidth(150)
        back_button = QtWidgets.QPushButton("Back")
        back_button.clicked.connect(self.on_back_button_pressed)
        back_button.setFixedWidth(150)
        button_layout.addWidget(reset_button)
        button_layout.addWidget(back_button)
        button_layout.addStretch()
        root_layout.addLayout(button_layout)
        self.controls_layout = QtWidgets.QVBoxLayout()
        self.init_settings_widgets()
        root_layout.addLayout(self.controls_layout)
        self.setLayout(root_layout)

    def on_reset_button_pressed(self):
        if self.settings.SETTINGS != self.original_settings:
            for k in self.original_settings.keys():
                self.settings.SETTINGS[k] = self.original_settings[k]
            self.star_system_picker.set_value(self.settings.SETTINGS[SettingsKeys.STAR_SYSTEM.value].value)
            self.centre_of_orbit_picker.set_choices(OrbitsPageSettings.CENTRE_OF_ORBIT_OPTIONS, 0)
            self.objects_to_show.set_value(self.settings.SETTINGS[SettingsKeys.OBJECTS_TO_SHOW.value])
            self.orbit_time_picker.set_value(self.settings.SETTINGS[SettingsKeys.ORBIT_TIME.value])
            self.num_orbits_picker.set_value(self.settings.SETTINGS[SettingsKeys.NUM_ORBITS.value])
            for widget in self.child_widgets:
                widget.set_state()

    def on_back_button_pressed(self):
        self.parent.switch_to(PageIndexes.ORBITS_PAGE.value, post_func=lambda w: w.update_graph())

    def init_settings_widgets(self):
        top_half = QtWidgets.QHBoxLayout()
        top_half.addStretch()
        self.star_system_picker = VerticalValuePicker(value_type="from_multiple",
                                                      lbl_text="Star system: ",
                                                      default_val="Solar System",
                                                      fixed_lbl_height=20,
                                                      choices=[k.value for k in solar_system_enum_to_class.keys()],
                                                      padding=[10, 10, 10, 10],
                                                      on_change=self.on_star_system_changed)
        self.star_system_picker.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        top_half.addLayout(self.star_system_picker)
        self.centre_of_orbit_picker = VerticalValuePicker(value_type="from_multiple",
                                                          lbl_text="Centre of orbit: ",
                                                          fixed_lbl_height=20,
                                                          choices=OrbitsPageSettings.CENTRE_OF_ORBIT_OPTIONS,
                                                          padding=[10, 10, 10, 10],
                                                          on_change=self.on_centre_of_orbit_changed)
        self.centre_of_orbit_picker.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.centre_of_orbit_picker.set_value(self.settings.SETTINGS[SettingsKeys.CENTRE_OF_ORBIT.value])
        top_half.addLayout(self.centre_of_orbit_picker)
        self.objects_to_show = VerticalValuePicker(value_type="many_from_multiple",
                                                   lbl_text="Objects to show: ",
                                                   choices=OrbitsPageSettings.OBJECTS_TO_SHOW_OPTIONS,
                                                   padding=[10, 10, 10, 10],
                                                   fixed_lbl_height=20,
                                                   on_change=self.on_object_to_show_checkbox_changed)
        self.objects_to_show.set_value(self.settings.SETTINGS[SettingsKeys.OBJECTS_TO_SHOW.value])
        self.objects_to_show.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        top_half.addLayout(self.objects_to_show)
        top_half.addStretch()
        self.controls_layout.addLayout(top_half)
        bottom_half = QtWidgets.QHBoxLayout()
        bottom_half.addStretch()
        view_type_picker = ViewTypePicker(self.settings,
                                          margin=[10, 10, 10, 10],
                                          alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        self.child_widgets.append(view_type_picker)
        bottom_half.addLayout(view_type_picker)
        self.orbit_time_picker = VerticalValuePicker(value_type=int,
                                                     lbl_text="Orbit time (s): ",
                                                     fixed_width=100,
                                                     tooltip="Orbit time for the longest orbit in seconds",
                                                     fixed_lbl_height=30,
                                                     fixed_form_height=30,
                                                     padding=[10, 10, 10, 10],
                                                     on_change=self.on_orbit_time_changed)
        self.orbit_time_picker.set_value(self.settings.SETTINGS[SettingsKeys.ORBIT_TIME.value])
        bottom_half.addLayout(self.orbit_time_picker)
        self.num_orbits_picker = VerticalValuePicker(value_type=int,
                                                     lbl_text="Number of orbits: ",
                                                     fixed_width=150,
                                                     fixed_lbl_height=30,
                                                     fixed_form_height=30,
                                                     padding=[10, 10, 10, 10],
                                                     on_change=self.on_num_orbits_changed)
        self.num_orbits_picker.set_value(self.settings.SETTINGS[SettingsKeys.NUM_ORBITS.value])
        bottom_half.addLayout(self.num_orbits_picker)
        bottom_half.addStretch()
        bottom_half.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.controls_layout.addLayout(bottom_half)
        self.controls_layout.setStretch(0, 0)
        self.controls_layout.setStretch(1, 1)

    def on_centre_of_orbit_changed(self, new_index: int):
        if new_index < 0 or not self.centre_of_orbit_picker.choices:
            return
        centre_name = self.centre_of_orbit_picker.choices[new_index]
        self.settings.SETTINGS[SettingsKeys.CENTRE_OF_ORBIT.value] = centre_name
        new_objects_to_show_options = [e.value for e in solar_system_enum_to_class[self.settings.SETTINGS[SettingsKeys.STAR_SYSTEM.value]].Planet]
        if centre_name in new_objects_to_show_options:
            new_objects_to_show_options.remove(centre_name)
        OrbitsPageSettings.OBJECTS_TO_SHOW_OPTIONS = new_objects_to_show_options
        self.objects_to_show.set_choices(new_objects_to_show_options)

    def on_object_to_show_checkbox_changed(self, checkboxes: list[QtWidgets.QCheckBox]):
        k = SettingsKeys.OBJECTS_TO_SHOW.value
        self.settings.SETTINGS[k] = [checkbox.text() for checkbox in checkboxes if checkbox.isChecked()]

    def on_orbit_time_changed(self, new_value: int):
        self.settings.SETTINGS[SettingsKeys.ORBIT_TIME.value] = new_value

    def on_num_orbits_changed(self, new_value: int):
        self.settings.SETTINGS[SettingsKeys.NUM_ORBITS.value] = new_value

    def on_star_system_changed(self, new_index: int):
        star_system: StarSystem = list(solar_system_enum_to_class.keys())[new_index]
        star_system_class = solar_system_enum_to_class[star_system]

        sun_name = star_system_class.Planet[star_system_class.SUN].value
        self.settings.SETTINGS[SettingsKeys.STAR_SYSTEM.value] = star_system
        self.settings.SETTINGS[SettingsKeys.CENTRE_OF_ORBIT.value] = sun_name
        new_objects_to_show = [e.value for e in star_system_class.Planet if e.name != star_system_class.SUN]
        OrbitsPageSettings.OBJECTS_TO_SHOW_OPTIONS = new_objects_to_show
        self.settings.SETTINGS[SettingsKeys.OBJECTS_TO_SHOW.value] = new_objects_to_show
        self.objects_to_show.set_choices(new_objects_to_show, check_all=True)
        OrbitsPageSettings.CENTRE_OF_ORBIT_OPTIONS = [e.value for e in star_system_class.Planet]
        self.centre_of_orbit_picker.set_choices(OrbitsPageSettings.CENTRE_OF_ORBIT_OPTIONS,
                                                0)


class SpirographPage(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setParent(parent)
        root_layout = QtWidgets.QHBoxLayout()
        self.sim_settings = OrbitSimSettings()
        self.fig = Figure(figsize=(10, 10))
        self.canvas = FigureCanvas(self.fig)
        self.graph_layout = QtWidgets.QVBoxLayout()
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.graph_layout.addWidget(self.toolbar)
        self.graph_layout.addWidget(self.canvas)
        self.anim = None
        root_layout.addLayout(self.graph_layout)
        controls_layout = QtWidgets.QVBoxLayout()
        self.planet1picker: HorizontalValuePicker = HorizontalValuePicker(
            value_type="from_multiple",
            lbl_text="Planet 1: ",
            default_val="Venus",
            choices=PLANETS,
            padding=[5, 5, 5, 5]
        )
        self.planet2picker: HorizontalValuePicker = HorizontalValuePicker(
            value_type="from_multiple",
            lbl_text="Planet 2: ",
            default_val="Earth",
            choices=PLANETS,
            padding=[5, 5, 5, 5]
        )
        self.speed_picker: HorizontalValuePicker = HorizontalValuePicker(
            value_type="from_multiple",
            lbl_text="Speed: ",
            tooltip="The speed at which a new line is drawn",
            choices=["slow", "medium", "fast"],
            fixed_form_width=75,
            fixed_lbl_width=20,
            fixed_height=20,
            padding=[5, 5, 5, 5])
        self.n_orbits: HorizontalValuePicker = HorizontalValuePicker(
            value_type=int,
            lbl_text="N: ",
            tooltip="Number of orbits of the outermost planet",
            fixed_form_width=100,
            fixed_lbl_width=20,
            fixed_height=20)

        param_picker_layout = QtWidgets.QVBoxLayout()
        planet_picker_layout = QtWidgets.QHBoxLayout()
        planet_picker_layout.addLayout(self.planet1picker)
        planet_picker_layout.addLayout(self.planet2picker)
        param_picker_layout.addLayout(planet_picker_layout)
        num_picker_layout = QtWidgets.QHBoxLayout()
        num_picker_layout.addLayout(self.speed_picker)
        num_picker_layout.addLayout(self.n_orbits)
        param_picker_layout.addLayout(num_picker_layout)
        param_picker_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        controls_layout.addStretch()
        controls_layout.addLayout(param_picker_layout)
        eval_button = QtWidgets.QPushButton("Evaluate")
        eval_button.pressed.connect(self.on_eval_button_press)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(eval_button)
        values_layout = QtWidgets.QHBoxLayout()
        self.completed_orbits = ValueViewer("Completed orbits",
                                            fixed_key_height=20,
                                            fixed_value_height=50,
                                            fixed_width=120,
                                            alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        self.elapsed_time = ValueViewer("Elapsed time",
                                        fixed_key_height=20,
                                        fixed_value_height=50,
                                        fixed_width=120,
                                        alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        values_layout.addLayout(self.completed_orbits)
        values_layout.addLayout(self.elapsed_time)
        values_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        controls_layout.addSpacing(20)
        controls_layout.addLayout(values_layout)
        controls_layout.addStretch()
        root_layout.addLayout(controls_layout)
        self.setLayout(root_layout)
        self.display_animation()

    def on_eval_button_press(self):
        print(self.planet1picker.get_value().upper(),
              self.planet2picker.get_value().upper(),
              self.speed_picker.get_value(),
              self.n_orbits.get_value())

    def display_animation(self):
        planet1: str = self.planet1picker.get_value().upper()
        planet2: str = self.planet2picker.get_value().upper()
        speed: str = self.speed_picker.get_value()
        N: int = int(self.speed_picker.get_value())
        if self.anim:
            self.anim.ani.event_source.stop()
        self.graph_layout.removeWidget(self.canvas)
        self.graph_layout.removeWidget(self.toolbar)
        self.fig = Figure(figsize=(10, 10))
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.graph_layout.insertWidget(0, self.toolbar)
        self.graph_layout.insertWidget(1, self.canvas)
        args = ["SOLAR_SYSTEM", "URANUS", "NEPTUNE", 10, "slow"]
        self.anim = SpiroAnimation(*args)


class PageClasses(Enum):
    ORBITS_PAGE = OrbitsPage
    ORBITS_PAGE_SETTINGS = OrbitsPageSettings
    SPIROGRAPH_PAGE = SpirographPage
