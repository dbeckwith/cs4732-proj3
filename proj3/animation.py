# -*- coding: utf-8 -*-

import os.path

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QBrush, QPainter
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView

from . import util


class Animation(object):
    """
    Abstract class for setting up a 2D scene and animating it.
    """

    def __init__(self, title, frame_rate, run_time):
        """
        Create a new Animation.

        Arguments:
            title: str, the window title
            frame_rate: float, the number of frames to display per second
            run_time: float, the number of seconds to run the animation
        """
        self.title = title
        assert 0 < frame_rate < 1000
        self.frame_rate = frame_rate
        assert run_time > 0
        self.run_time = run_time

        self.frame = 0
        self.prev_update_time = None

        self.scene = QGraphicsScene()

        # create the window
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.view.setWindowTitle(self.title)

    def setup_scene(self, background_color):
        """
        Sets up the scene. Should be called before running the animation.

        Arguments:
            background_color: QColor, background color of the scene
        """
        # set background color
        self.view.setBackgroundBrush(QBrush(background_color))

        # let subclass populate scene
        self.make_scene()

    def make_scene(self):
        """
        Abstract method. Populates the scene with objects.
        """
        raise NotImplementedError()

    def _update(self):
        """
        Updates the animation, rendering the next frame.
        """
        # current animation time in seconds
        t = util.lerp(self.frame, 0, self.frame_rate, 0, 1)
        # change in time since the last frame
        dt = 1 / self.frame_rate if self.prev_update_time is None else t - self.prev_update_time
        # call subclass's frame update
        self.update(self.frame, t, dt)

        # stop the animation and close the window if run past run_time
        if t >= self.run_time:
            self.animation_timer.stop()
            self.view.close()

        self.prev_update_time = t
        self.frame += 1

    def update(self, frame, t, dt):
        """
        Abstract method. Updates one frame of the animation.

        Arguments:
            frame: int, the current frame number
            t: float, the current animation time in seconds
            dt: float, the number of seconds since the last update
        """
        raise NotImplementedError()

    def run(self):
        """
        Runs the animation asynchronously. The animation runs in the background for self.run_time seconds.
        """
        self.animation_timer = QTimer(self.view)
        # timer interval in msecs
        self.animation_timer.setInterval(1000 / self.frame_rate)
        # call update on each timeout of the timer
        self.animation_timer.timeout.connect(self._update)
        self.animation_timer.start()

        # show the main window
        self.view.show()
