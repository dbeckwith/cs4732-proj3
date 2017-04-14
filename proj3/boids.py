# -*- coding: utf-8 -*-

import math
import random
import itertools

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPolygonF, QPen, QBrush

from . import util


class BoidSim(object):
    # TODO: obstacles
    
    team_attractions = {
        'red': 'blue',
        'blue': 'green',
        'green': 'red'
    }
    team_evasions = {
        'red': 'green',
        'blue': 'red',
        'green': 'blue'
    }

    def __init__(self, scene, bounds_radius):
        self.scene = scene
        self.bounds_radius = bounds_radius
        self.boids = set()
        for team in Boid.team_colors.keys():
            for _ in range(30):
                pr = random.random() * bounds_radius
                pt = random.random() * math.pi * 2
                vr = Boid.speed
                vt = random.random() * math.pi * 2
                self.boids.add(Boid(self,
                    team,
                    QPointF(pr * math.cos(pt), pr * math.sin(pt)),
                    QPointF(vr * math.cos(vt), vr * math.sin(vt))))

    def update(self, dt):
        for boid in self.boids:
            boid.acceleration = QPointF()

            bounds_repel = util.lerp(util.length(boid.position), self.bounds_radius * 0.9, self.bounds_radius, 0, 2000, True) * -util.normalized_or_null(boid.position)
            boid.acceleration += bounds_repel

            boid.neighborhood = set(neighbor for neighbor in self.boids if \
                neighbor != boid and \
                neighbor.team == boid.team and \
                util.lengthsq(neighbor.position - boid.position) < boid.visual_range ** 2)
            if boid.neighborhood:
                separation = sum((boid.position - neighbor.position for neighbor in boid.neighborhood if \
                    boid.team == neighbor.team or \
                    self.team_evasions[boid.team] == neighbor.team), QPointF())
                boid.acceleration += separation / 30 * 60

                avg_heading = sum((neighbor.velocity for neighbor in boid.neighborhood), QPointF()) / len(boid.neighborhood)
                alignment = avg_heading - boid.velocity
                boid.acceleration += alignment / 8 * 60

                avg_position = sum((neighbor.position for neighbor in boid.neighborhood if \
                    boid.team == neighbor.team or \
                    self.team_attractions[boid.team] == neighbor.team), QPointF()) / len(boid.neighborhood)
                cohesion = avg_position - boid.position
                boid.acceleration += cohesion / 100 * 60

        for boid in self.boids:
            boid.update(dt)

        for (boid1, boid2) in itertools.combinations(self.boids, 2):
            dpos = boid2.position - boid1.position
            if util.lengthsq(boid2.position - boid1.position) < (boid1.collision_radius + boid2.collision_radius) ** 2:
                boid1_facing = QPointF.dotProduct(dpos, boid1.velocity) > 0
                boid2_facing = QPointF.dotProduct(dpos, boid2.velocity) < 0
                if boid1_facing and not boid2_facing:
                    predator = boid1
                    prey = boid2
                elif boid2_facing and not boid1_facing:
                    predator = boid2
                    prey = boid1
                else:
                    predator, prey = random.sample([boid1, boid2], 2)
                prey.team = predator.team


class Boid(object):
    speed = 100
    visual_range = 50
    collision_radius = 10
    team_colors = {
        'red': 0,
        'green': 120,
        'blue': 240
    }

    def __init__(self, sim, team, position, velocity):
        self.sim = sim

        self.team = team

        self.position = position
        self.velocity = velocity

        self.body_graphic = sim.scene.addPolygon(
            QPolygonF([
                QPointF(1, 0),
                QPointF(-0.6, 0.6),
                QPointF(-0.3, 0),
                QPointF(-0.6, -0.6)]),
            QPen(Qt.NoPen),
            QBrush())
        self.body_graphic.setScale(self.collision_radius)

        self.visual_range_graphic = sim.scene.addEllipse(
            -self.visual_range, -self.visual_range,
            self.visual_range * 2, self.visual_range * 2,
            QPen(util.hsl(0, 0, 0, 20)),
            QBrush())
        self.visual_range_graphic.setVisible(False)

        self.graphics_group = sim.scene.createItemGroup([
            self.body_graphic,
            self.visual_range_graphic])

        self._update_graphics()

    def _update_graphics(self):
        self.graphics_group.setX(self.position.x())
        self.graphics_group.setY(self.position.y())
        self.body_graphic.setRotation(util.rad2deg(math.atan2(self.velocity.y(), self.velocity.x())))
        self.body_graphic.setBrush(QBrush(util.hsl(self.team_colors[self.team], 90, 80)))

    def update(self, dt):
        self.velocity += self.acceleration * dt
        self.velocity = util.normalized(self.velocity) * self.speed

        self.position += self.velocity * dt
        if util.lengthsq(self.position) > self.sim.bounds_radius ** 2:
            self.position /= util.length(self.position)
            self.velocity = self.velocity - 2 * QPointF.dotProduct(self.velocity, self.position) * self.position
            self.position *= self.sim.bounds_radius

        self._update_graphics()
